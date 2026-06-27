from __future__ import annotations

import asyncio
from dataclasses import dataclass
import os
from pathlib import Path
import platform
import shlex
import socket
import subprocess
import sys
import textwrap
import time
from typing import Awaitable, Callable

from .adapters import ShellAdapter
from .models import CommandResult, FixtureResult, FixtureStatus


FixtureFunc = Callable[[ShellAdapter, Path], Awaitable[FixtureResult]]


@dataclass(frozen=True)
class Fixture:
    name: str
    summary: str
    public_pain: str
    max_seconds: float
    run: FixtureFunc


def fixture_names() -> list[str]:
    return [fixture.name for fixture in FIXTURES]


def select_fixtures(names: list[str] | None) -> list[Fixture]:
    if not names:
        return list(FIXTURES)
    by_name = {fixture.name: fixture for fixture in FIXTURES}
    missing = sorted(set(names) - set(by_name))
    if missing:
        raise ValueError(f"Unknown fixture(s): {', '.join(missing)}")
    return [by_name[name] for name in names]


async def timeout_child_pipe(adapter: ShellAdapter, workdir: Path) -> FixtureResult:
    start = time.monotonic()
    code = """
import subprocess
import sys
import time
child = subprocess.Popen([sys.executable, "-c", "import sys,time; print('ASC_CHILD_READY', flush=True); time.sleep(10)"])
print("ASC_PARENT_READY", flush=True)
time.sleep(10)
"""
    result = await adapter.run(_py(code), cwd=workdir, timeout_seconds=0.5)
    if not result.timed_out:
        return _result("timeout-child-pipe", adapter, FixtureStatus.FAIL, start, "command did not time out", result=result)
    if result.duration_seconds > 3.0:
        return _result("timeout-child-pipe", adapter, FixtureStatus.FAIL, start, "timeout return was not bounded", result=result)
    return _result("timeout-child-pipe", adapter, FixtureStatus.PASS, start, "timeout returned without hanging on child pipes", result=result)


async def timeout_process_tree(adapter: ShellAdapter, workdir: Path) -> FixtureResult:
    start = time.monotonic()
    pid_file = workdir / "child.pid"
    code = f"""
import pathlib
import subprocess
import sys
import time
child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(10)"])
pathlib.Path({str(pid_file)!r}).write_text(str(child.pid))
print("ASC_CHILD_PID", child.pid, flush=True)
time.sleep(10)
"""
    result = await adapter.run(_py(code), cwd=workdir, timeout_seconds=0.5)
    if not result.timed_out:
        return _result("timeout-process-tree", adapter, FixtureStatus.FAIL, start, "command did not time out", result=result)
    pid = _read_pid(pid_file)
    if pid is None:
        return _result("timeout-process-tree", adapter, FixtureStatus.ERROR, start, "fixture did not record child pid", result=result)
    await asyncio.sleep(0.2)
    if _pid_alive(pid):
        return _result(
            "timeout-process-tree",
            adapter,
            FixtureStatus.FAIL,
            start,
            "child process survived adapter timeout",
            result=result,
            child_pid=pid,
        )
    return _result(
        "timeout-process-tree",
        adapter,
        FixtureStatus.PASS,
        start,
        "timeout terminated the owned process tree",
        result=result,
        child_pid=pid,
    )


async def background_server_lifecycle(adapter: ShellAdapter, workdir: Path) -> FixtureResult:
    start = time.monotonic()
    if not adapter.capabilities.supports_background:
        return _result(
            "background-server-lifecycle",
            adapter,
            FixtureStatus.UNSUPPORTED,
            start,
            "adapter does not declare background command support",
        )
    port = _free_port()
    command = _py(
        f"""
import http.server
import socketserver
socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("127.0.0.1", {port}), http.server.SimpleHTTPRequestHandler) as server:
    print("ASC_SERVER_READY {port}", flush=True)
    server.serve_forever()
"""
    )
    handle = await adapter.start_background(command, cwd=workdir)
    started = await _wait_until(lambda: _port_open(port), timeout_seconds=3.0)
    status = await adapter.check_background(handle)
    stop = await adapter.stop_background(handle)
    closed = await _wait_until(lambda: not _port_open(port), timeout_seconds=3.0)
    if not started:
        return _result(
            "background-server-lifecycle",
            adapter,
            FixtureStatus.FAIL,
            start,
            "background server did not open its owned port",
            handle=handle,
            bg_status=status,
            stop=stop,
            port=port,
        )
    if not closed:
        return _result(
            "background-server-lifecycle",
            adapter,
            FixtureStatus.FAIL,
            start,
            "owned background port stayed open after stop",
            handle=handle,
            bg_status=status,
            stop=stop,
            port=port,
        )
    return _result(
        "background-server-lifecycle",
        adapter,
        FixtureStatus.PASS,
        start,
        "background start/check/stop closed the owned port",
        handle=handle,
        bg_status=status,
        stop=stop,
        port=port,
    )


async def output_before_exit(adapter: ShellAdapter, workdir: Path) -> FixtureResult:
    start = time.monotonic()
    result = await adapter.run(
        _py(
            """
import sys
print("ASC_STDOUT_BEFORE_EXIT")
print("ASC_STDERR_BEFORE_EXIT", file=sys.stderr)
raise SystemExit(7)
"""
        ),
        cwd=workdir,
        timeout_seconds=3.0,
    )
    output = result.combined_output()
    if result.exit_code != 7:
        return _result("output-before-exit", adapter, FixtureStatus.FAIL, start, "non-zero exit code was not preserved", result=result)
    if "ASC_STDOUT_BEFORE_EXIT" not in output or "ASC_STDERR_BEFORE_EXIT" not in output:
        return _result("output-before-exit", adapter, FixtureStatus.FAIL, start, "stdout or stderr marker was lost", result=result)
    return _result("output-before-exit", adapter, FixtureStatus.PASS, start, "stdout, stderr, and exit status survived", result=result)


async def output_after_kill(adapter: ShellAdapter, workdir: Path) -> FixtureResult:
    start = time.monotonic()
    result = await adapter.run(
        _py(
            """
import sys
import time
print("ASC_STDOUT_BEFORE_KILL", flush=True)
print("ASC_STDERR_BEFORE_KILL", file=sys.stderr, flush=True)
time.sleep(10)
"""
        ),
        cwd=workdir,
        timeout_seconds=1.0,
    )
    output = result.combined_output()
    if not result.timed_out:
        return _result("output-after-kill", adapter, FixtureStatus.FAIL, start, "command did not time out", result=result)
    if "ASC_STDOUT_BEFORE_KILL" not in output and "ASC_STDERR_BEFORE_KILL" not in output:
        return _result("output-after-kill", adapter, FixtureStatus.FAIL, start, "bounded pre-kill output was lost", result=result)
    return _result("output-after-kill", adapter, FixtureStatus.PASS, start, "bounded pre-kill output remained available", result=result)


async def cwd_isolation(adapter: ShellAdapter, workdir: Path) -> FixtureResult:
    start = time.monotonic()
    nested = workdir / "nested"
    nested.mkdir()
    before = await adapter.run(_py("import os; print(os.getcwd())"), cwd=workdir, timeout_seconds=3.0)
    cd_result = await adapter.run("cd nested", cwd=workdir, timeout_seconds=3.0)
    after = await adapter.run(_py("import os; print(os.getcwd())"), cwd=workdir, timeout_seconds=3.0)
    expected = str(workdir)
    if expected not in before.combined_output():
        return _result("cwd-isolation", adapter, FixtureStatus.ERROR, start, "fixture could not observe initial cwd", before=before)
    if adapter.capabilities.supports_sticky_cwd:
        summary = "adapter declares sticky cwd support; command behavior recorded"
        status = FixtureStatus.PASS
    elif expected in after.combined_output():
        summary = "cwd stayed isolated across commands"
        status = FixtureStatus.PASS
    else:
        summary = "cwd changed across commands without sticky cwd declaration"
        status = FixtureStatus.FAIL
    return _result("cwd-isolation", adapter, status, start, summary, before=before, cd_result=cd_result, after=after)


async def env_boundary(adapter: ShellAdapter, workdir: Path) -> FixtureResult:
    start = time.monotonic()
    if not adapter.capabilities.supports_env_override:
        return _result("env-boundary", adapter, FixtureStatus.UNSUPPORTED, start, "adapter does not declare env override support")
    env = _minimal_env()
    env.pop("ASC_SENTINEL_SECRET", None)
    previous = os.environ.get("ASC_SENTINEL_SECRET")
    os.environ["ASC_SENTINEL_SECRET"] = "must-not-leak"
    try:
        result = await adapter.run(
            _py(
                """
import os
print("ASC_ENV_PRESENT" if "ASC_SENTINEL_SECRET" in os.environ else "ASC_ENV_ABSENT")
"""
            ),
            cwd=workdir,
            env=env,
            timeout_seconds=3.0,
        )
    finally:
        if previous is None:
            os.environ.pop("ASC_SENTINEL_SECRET", None)
        else:
            os.environ["ASC_SENTINEL_SECRET"] = previous
    if "ASC_ENV_ABSENT" not in result.combined_output():
        return _result("env-boundary", adapter, FixtureStatus.FAIL, start, "explicit env boundary leaked host sentinel", result=result)
    return _result("env-boundary", adapter, FixtureStatus.PASS, start, "explicit env boundary excluded host sentinel", result=result)


async def pty_detection(adapter: ShellAdapter, workdir: Path) -> FixtureResult:
    start = time.monotonic()
    result = await adapter.run(
        _py(
            """
import os
print(f"ASC_STDIN_TTY={os.isatty(0)}")
print(f"ASC_STDOUT_TTY={os.isatty(1)}")
"""
        ),
        cwd=workdir,
        timeout_seconds=3.0,
    )
    output = result.combined_output()
    stdout_tty = "ASC_STDOUT_TTY=True" in output
    declared = adapter.capabilities.allocates_pty
    if declared is None:
        return _result("pty-detection", adapter, FixtureStatus.UNSUPPORTED, start, "adapter does not declare PTY behavior", result=result)
    if stdout_tty != declared:
        return _result("pty-detection", adapter, FixtureStatus.FAIL, start, "observed PTY behavior did not match adapter declaration", result=result)
    return _result("pty-detection", adapter, FixtureStatus.PASS, start, "observed PTY behavior matched adapter declaration", result=result)


async def windows_tree_termination(adapter: ShellAdapter, workdir: Path) -> FixtureResult:
    start = time.monotonic()
    if platform.system().lower() != "windows":
        return _result("windows-tree-termination", adapter, FixtureStatus.SKIP, start, "Windows-only fixture skipped on this host")
    return await timeout_process_tree(adapter, workdir)


FIXTURES: tuple[Fixture, ...] = (
    Fixture("timeout-child-pipe", "timeout returns even when child keeps pipes open", "Codex timeout hangs with child stdout/stderr pipes", 5.0, timeout_child_pipe),
    Fixture("timeout-process-tree", "timeout terminates the owned process tree", "Codex/Claude child process leaks after timeout", 5.0, timeout_process_tree),
    Fixture("background-server-lifecycle", "background server start/check/stop closes port", "Claude/Copilot long-running dev-server lifecycle failures", 8.0, background_server_lifecycle),
    Fixture("output-before-exit", "normal completion preserves stdout, stderr, and exit code", "Copilot terminal output not received", 5.0, output_before_exit),
    Fixture("output-after-kill", "timeout preserves bounded pre-kill output", "timeout or kill loses final useful output", 5.0, output_after_kill),
    Fixture("cwd-isolation", "cwd behavior is isolated or explicitly sticky", "Copilot/VS Code cwd confusion", 5.0, cwd_isolation),
    Fixture("env-boundary", "explicit env excludes host sentinel", "shell subprocess inherits unexpected host env", 5.0, env_boundary),
    Fixture("pty-detection", "PTY allocation is observable and declared", "Codex no-TTY execution surprises", 5.0, pty_detection),
    Fixture("windows-tree-termination", "Windows process-tree timeout behavior", "Claude Windows background process remains alive", 5.0, windows_tree_termination),
)


def _py(code: str) -> str:
    normalized = textwrap.dedent(code).strip()
    args = [sys.executable, "-c", normalized]
    if os.name == "nt":
        return subprocess.list2cmdline(args)
    return shlex.join(args)


def _minimal_env() -> dict[str, str]:
    keep = ["PATH", "SYSTEMROOT", "WINDIR", "TMPDIR", "TEMP", "TMP"]
    return {name: value for name, value in os.environ.items() if name in keep}


def _result(
    fixture: str,
    adapter: ShellAdapter,
    status: FixtureStatus,
    start: float,
    summary: str,
    **evidence: object,
) -> FixtureResult:
    details = []
    for key, value in evidence.items():
        if isinstance(value, CommandResult):
            details.append(f"{key}: exit={value.exit_code} timed_out={value.timed_out} duration={value.duration_seconds:.3f}s")
        else:
            details.append(f"{key}: {value}")
    return FixtureResult(
        fixture=fixture,
        adapter=adapter.name,
        status=status,
        summary=summary,
        duration_seconds=time.monotonic() - start,
        details=details,
        evidence=evidence,
    )


def _read_pid(path: Path) -> int | None:
    try:
        return int(path.read_text().strip())
    except (OSError, ValueError):
        return None


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "posix":
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True
    completed = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True, check=False)
    return str(pid) in completed.stdout


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex(("127.0.0.1", port)) == 0


async def _wait_until(predicate: Callable[[], bool], *, timeout_seconds: float) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if predicate():
            return True
        await asyncio.sleep(0.05)
    return predicate()

from __future__ import annotations

import asyncio
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import tempfile
import time
from typing import Protocol

from .models import AdapterCapabilities, BackgroundHandle, BackgroundStatus, CommandResult


class ShellAdapter(Protocol):
    name: str
    capabilities: AdapterCapabilities

    async def run(
        self,
        command: str,
        *,
        cwd: Path,
        env: dict[str, str] | None = None,
        timeout_seconds: float = 10.0,
    ) -> CommandResult:
        ...

    async def start_background(
        self,
        command: str,
        *,
        cwd: Path,
        env: dict[str, str] | None = None,
    ) -> BackgroundHandle:
        ...

    async def check_background(self, handle: BackgroundHandle) -> BackgroundStatus:
        ...

    async def stop_background(self, handle: BackgroundHandle, *, timeout_seconds: float = 5.0) -> CommandResult:
        ...

    async def cleanup(self) -> None:
        ...


class ReferenceSubprocessAdapter:
    name = "subprocess-reference"

    def __init__(self) -> None:
        self.capabilities = AdapterCapabilities(name=self.name)
        self._background: dict[str, tuple[subprocess.Popen[bytes], Path, Path]] = {}
        self._tmpdir = Path(tempfile.mkdtemp(prefix="asc-bg-"))

    async def run(
        self,
        command: str,
        *,
        cwd: Path,
        env: dict[str, str] | None = None,
        timeout_seconds: float = 10.0,
    ) -> CommandResult:
        start = time.monotonic()
        proc = await asyncio.create_subprocess_shell(
            command,
            cwd=str(cwd),
            env=_resolve_env(env),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            **_session_kwargs(),
        )
        stdout_task = asyncio.create_task(_read_stream(proc.stdout))
        stderr_task = asyncio.create_task(_read_stream(proc.stderr))
        timed_out = False
        try:
            await asyncio.wait_for(proc.wait(), timeout_seconds)
        except asyncio.TimeoutError:
            timed_out = True
            await _terminate_async_process(proc, graceful=True)
            try:
                await asyncio.wait_for(proc.wait(), 2.0)
            except asyncio.TimeoutError:
                await _terminate_async_process(proc, graceful=False)
                await asyncio.wait_for(proc.wait(), 2.0)
        stdout_bytes = await _collect_stream(stdout_task)
        stderr_bytes = await _collect_stream(stderr_task)
        return CommandResult(
            stdout=_decode(stdout_bytes),
            stderr=_decode(stderr_bytes),
            exit_code=proc.returncode,
            timed_out=timed_out,
            duration_seconds=time.monotonic() - start,
        )

    async def start_background(
        self,
        command: str,
        *,
        cwd: Path,
        env: dict[str, str] | None = None,
    ) -> BackgroundHandle:
        ident = f"bg-{len(self._background) + 1}"
        stdout_path = self._tmpdir / f"{ident}.stdout"
        stderr_path = self._tmpdir / f"{ident}.stderr"
        with stdout_path.open("wb") as stdout_file, stderr_path.open("wb") as stderr_file:
            proc: subprocess.Popen[bytes] = subprocess.Popen(
                command,
                shell=True,
                cwd=str(cwd),
                env=_resolve_env(env),
                stdout=stdout_file,
                stderr=stderr_file,
                **_popen_session_kwargs(),
            )
        self._background[ident] = (proc, stdout_path, stderr_path)
        return BackgroundHandle(id=ident, pid=proc.pid, command=command)

    async def check_background(self, handle: BackgroundHandle) -> BackgroundStatus:
        proc, stdout_path, stderr_path = self._background[handle.id]
        exit_code = proc.poll()
        return BackgroundStatus(
            running=exit_code is None,
            stdout=_read_text(stdout_path),
            stderr=_read_text(stderr_path),
            exit_code=exit_code,
        )

    async def stop_background(self, handle: BackgroundHandle, *, timeout_seconds: float = 5.0) -> CommandResult:
        start = time.monotonic()
        proc, stdout_path, stderr_path = self._background.pop(handle.id)
        await asyncio.to_thread(_terminate_popen, proc, timeout_seconds)
        return CommandResult(
            stdout=_read_text(stdout_path),
            stderr=_read_text(stderr_path),
            exit_code=proc.poll(),
            duration_seconds=time.monotonic() - start,
        )

    async def cleanup(self) -> None:
        for ident in list(self._background):
            proc, _, _ = self._background.pop(ident)
            await asyncio.to_thread(_terminate_popen, proc, 1.0)
        shutil.rmtree(self._tmpdir, ignore_errors=True)


class PydanticAIHarnessAdapter:
    name = "pydantic-ai-harness"

    def __init__(self) -> None:
        self.capabilities = AdapterCapabilities(
            name=self.name,
            supports_background=True,
            supports_env_override=True,
            supports_sticky_cwd=True,
        )
        try:
            from pydantic_ai_harness import Shell
        except ImportError as exc:  # pragma: no cover - depends on optional package
            raise RuntimeError(
                "pydantic-ai-harness is not installed. Install with "
                "`python3 -m pip install '.[pydantic-ai-harness]'`."
            ) from exc

        self._Shell = Shell
        self._toolsets: dict[tuple[str, tuple[tuple[str, str], ...] | None], object] = {}
        self._background_toolsets: dict[str, object] = {}

    async def run(
        self,
        command: str,
        *,
        cwd: Path,
        env: dict[str, str] | None = None,
        timeout_seconds: float = 10.0,
    ) -> CommandResult:
        start = time.monotonic()
        toolset = self._toolset(cwd, env)
        raw = await toolset.run_command(command, timeout_seconds=timeout_seconds)  # type: ignore[attr-defined]
        return _parse_pydantic_command(raw, time.monotonic() - start)

    async def start_background(
        self,
        command: str,
        *,
        cwd: Path,
        env: dict[str, str] | None = None,
    ) -> BackgroundHandle:
        toolset = self._toolset(cwd, env)
        raw = await toolset.start_command(command)  # type: ignore[attr-defined]
        match = re.search(r"ID:\s*([A-Za-z0-9_-]+)", raw)
        if not match:
            raise RuntimeError(f"Could not parse Pydantic AI Harness background ID from: {raw!r}")
        command_id = match.group(1)
        self._background_toolsets[command_id] = toolset
        return BackgroundHandle(id=command_id, command=command, raw=raw)

    async def check_background(self, handle: BackgroundHandle) -> BackgroundStatus:
        toolset = self._background_toolsets[handle.id]
        raw = await toolset.check_command(handle.id)  # type: ignore[attr-defined]
        return _parse_pydantic_background(raw)

    async def stop_background(self, handle: BackgroundHandle, *, timeout_seconds: float = 5.0) -> CommandResult:
        start = time.monotonic()
        toolset = self._background_toolsets.pop(handle.id)
        raw = await toolset.stop_command(handle.id)  # type: ignore[attr-defined]
        parsed = _parse_pydantic_command(raw, time.monotonic() - start)
        return parsed

    async def cleanup(self) -> None:
        for toolset in self._toolsets.values():
            exit_fn = getattr(toolset, "__aexit__", None)
            if exit_fn is not None:
                await exit_fn(None, None, None)
        self._toolsets.clear()
        self._background_toolsets.clear()

    def _toolset(self, cwd: Path, env: dict[str, str] | None) -> object:
        key = (str(cwd), tuple(sorted(env.items())) if env is not None else None)
        toolset = self._toolsets.get(key)
        if toolset is None:
            shell = self._Shell(cwd=cwd, env=env, denied_commands=[], default_timeout=10.0)
            toolset = shell.get_toolset()
            self._toolsets[key] = toolset
        return toolset


def build_adapter(name: str) -> ShellAdapter:
    if name == ReferenceSubprocessAdapter.name:
        return ReferenceSubprocessAdapter()
    if name == PydanticAIHarnessAdapter.name:
        return PydanticAIHarnessAdapter()
    if name == "acp-local-terminal":
        from .acp_local import ACPLocalTerminalAdapter

        return ACPLocalTerminalAdapter()
    if name == "codex-app-server":
        from .codex_app_server import CodexAppServerAdapter

        return CodexAppServerAdapter()
    raise ValueError(f"Unknown adapter: {name}")


def available_adapters() -> list[str]:
    return [
        ReferenceSubprocessAdapter.name,
        PydanticAIHarnessAdapter.name,
        "acp-local-terminal",
        "codex-app-server",
    ]


def _resolve_env(env: dict[str, str] | None) -> dict[str, str] | None:
    if env is None:
        return None
    return dict(env)


def _session_kwargs() -> dict[str, object]:
    if os.name == "posix":
        return {"start_new_session": True}
    if os.name == "nt":
        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    return {}


def _popen_session_kwargs() -> dict[str, object]:
    return _session_kwargs()


async def _terminate_async_process(proc: asyncio.subprocess.Process, *, graceful: bool) -> None:
    if os.name == "posix":
        sig = signal.SIGTERM if graceful else signal.SIGKILL
        try:
            os.killpg(proc.pid, sig)
        except ProcessLookupError:
            return
    elif os.name == "nt":
        # Terminating the shell PID alone leaves Python children alive on Windows.
        # taskkill's tree mode is the Windows equivalent of killing the POSIX
        # process group created above.
        await asyncio.to_thread(_terminate_windows_process_tree, proc.pid)
    else:
        if graceful:
            proc.terminate()
        else:
            proc.kill()


def _terminate_popen(proc: subprocess.Popen[bytes], timeout_seconds: float) -> None:
    if proc.poll() is not None:
        return
    if os.name == "posix":
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
    elif os.name == "nt":
        _terminate_windows_process_tree(proc.pid)
    else:
        proc.terminate()
    try:
        proc.wait(timeout=timeout_seconds)
        return
    except subprocess.TimeoutExpired:
        pass
    if os.name == "posix":
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            return
    elif os.name == "nt":
        _terminate_windows_process_tree(proc.pid)
    else:
        proc.kill()
    try:
        proc.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        pass


def _terminate_windows_process_tree(pid: int) -> None:
    if pid <= 0:
        return
    try:
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            capture_output=True,
            check=False,
            timeout=5.0,
        )
    except (OSError, subprocess.TimeoutExpired):
        # The caller still waits for the original process and can report a
        # failed fixture if a child remains alive.
        return


def _decode(data: bytes | None) -> str:
    if data is None:
        return ""
    return data.decode("utf-8", errors="replace")


async def _read_stream(stream: asyncio.StreamReader | None) -> bytes:
    if stream is None:
        return b""
    return await stream.read()


async def _collect_stream(task: asyncio.Task[bytes]) -> bytes:
    try:
        return await asyncio.wait_for(task, 2.0)
    except asyncio.TimeoutError:
        task.cancel()
        return b""


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _parse_pydantic_command(raw: str, duration_seconds: float) -> CommandResult:
    exit_code: int | None = 0
    exit_match = re.search(r"\[exit code:\s*(-?\d+)\]", raw)
    if exit_match:
        exit_code = int(exit_match.group(1))
    timed_out = raw.startswith("[Command timed out after ")
    if timed_out:
        exit_code = None
    stdout = _extract_section(raw, "stdout")
    stderr = _extract_section(raw, "stderr")
    return CommandResult(
        stdout=stdout,
        stderr=stderr,
        exit_code=exit_code,
        timed_out=timed_out,
        duration_seconds=duration_seconds,
        raw=raw,
    )


def _parse_pydantic_background(raw: str) -> BackgroundStatus:
    running = "[status: running]" in raw
    exit_code: int | None = None
    exit_match = re.search(r"\[exit code:\s*(-?\d+)\]", raw)
    if exit_match:
        exit_code = int(exit_match.group(1))
    return BackgroundStatus(
        running=running,
        stdout=_extract_section(raw, "stdout"),
        stderr=_extract_section(raw, "stderr"),
        exit_code=exit_code,
        raw=raw,
    )


def _extract_section(raw: str, name: str) -> str:
    marker = f"[{name}]\n"
    start = raw.find(marker)
    if start == -1:
        return ""
    start += len(marker)
    next_markers = [idx for idx in (raw.find("\n[stderr]", start), raw.find("\n[exit code:", start)) if idx != -1]
    end = min(next_markers) if next_markers else len(raw)
    return raw[start:end].strip("\n")

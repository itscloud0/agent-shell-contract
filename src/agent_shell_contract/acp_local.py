from __future__ import annotations

import asyncio
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import time

from .models import AdapterCapabilities, BackgroundHandle, BackgroundStatus, CommandResult


class ACPLocalTerminalAdapter:
    """Adapter that exercises ACP terminal method semantics without model calls.

    The implementation uses the official `agent-client-protocol` schema package
    and a local in-process terminal client. It validates the ACP adapter shape;
    it is not a claim that a specific ACP client implementation has passed.
    """

    name = "acp-local-terminal"

    def __init__(self) -> None:
        try:
            from acp import schema
        except ImportError as exc:  # pragma: no cover - depends on optional package
            raise RuntimeError(
                "agent-client-protocol is not installed. Install with "
                "`python3 -m pip install '.[acp]'`."
            ) from exc

        self.capabilities = AdapterCapabilities(
            name=self.name,
            supports_background=True,
            supports_env_override=True,
            supports_sticky_cwd=False,
        )
        self._schema = schema
        self._client = _LocalACPClient(schema)
        self._session_id = "agent-shell-contract-local"

    async def run(
        self,
        command: str,
        *,
        cwd: Path,
        env: dict[str, str] | None = None,
        timeout_seconds: float = 10.0,
    ) -> CommandResult:
        start = time.monotonic()
        response = self._client.create_terminal(
            command=command,
            session_id=self._session_id,
            cwd=str(cwd),
            env=_to_acp_env(self._schema, env),
        )
        terminal_id = response.terminal_id
        timed_out = False
        try:
            exit_response = await asyncio.wait_for(
                asyncio.to_thread(self._client.wait_for_terminal_exit, self._session_id, terminal_id),
                timeout_seconds,
            )
        except asyncio.TimeoutError:
            timed_out = True
            self._client.kill_terminal(self._session_id, terminal_id)
            exit_response = await asyncio.to_thread(self._client.wait_for_terminal_exit, self._session_id, terminal_id)
        output = self._client.terminal_output(self._session_id, terminal_id).output
        self._client.release_terminal(self._session_id, terminal_id)
        return CommandResult(
            stdout=output,
            stderr="",
            exit_code=_exit_code_from_acp(exit_response),
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
        response = self._client.create_terminal(
            command=command,
            session_id=self._session_id,
            cwd=str(cwd),
            env=_to_acp_env(self._schema, env),
        )
        return BackgroundHandle(id=response.terminal_id, command=command)

    async def check_background(self, handle: BackgroundHandle) -> BackgroundStatus:
        output = self._client.terminal_output(self._session_id, handle.id)
        exit_code = _exit_status_code(output.exit_status)
        return BackgroundStatus(
            running=output.exit_status is None,
            stdout=output.output,
            stderr="",
            exit_code=exit_code,
        )

    async def stop_background(self, handle: BackgroundHandle, *, timeout_seconds: float = 5.0) -> CommandResult:
        start = time.monotonic()
        self._client.kill_terminal(self._session_id, handle.id)
        exit_response = await asyncio.to_thread(self._client.wait_for_terminal_exit, self._session_id, handle.id)
        output = self._client.terminal_output(self._session_id, handle.id).output
        self._client.release_terminal(self._session_id, handle.id)
        return CommandResult(
            stdout=output,
            stderr="",
            exit_code=_exit_code_from_acp(exit_response),
            duration_seconds=time.monotonic() - start,
        )

    async def cleanup(self) -> None:
        await asyncio.to_thread(self._client.cleanup)


class _LocalACPClient:
    def __init__(self, schema: object) -> None:
        self._schema = schema
        self._terminals: dict[str, _Terminal] = {}
        self._tmpdir = Path(tempfile.mkdtemp(prefix="asc-acp-"))
        self._counter = 0

    def create_terminal(
        self,
        *,
        command: str,
        session_id: str,
        args: list[str] | None = None,
        cwd: str | None = None,
        env: list[object] | None = None,
        output_byte_limit: int | None = None,
        **_: object,
    ) -> object:
        del session_id, args, output_byte_limit
        self._counter += 1
        terminal_id = f"terminal-{self._counter}"
        output_path = self._tmpdir / f"{terminal_id}.output"
        output_file = output_path.open("wb")
        proc = subprocess.Popen(
            command,
            shell=True,
            cwd=cwd,
            env=_from_acp_env(env),
            stdout=output_file,
            stderr=subprocess.STDOUT,
            **_popen_session_kwargs(),
        )
        output_file.close()
        self._terminals[terminal_id] = _Terminal(proc=proc, output_path=output_path)
        return self._schema.CreateTerminalResponse(terminalId=terminal_id)

    def terminal_output(self, session_id: str, terminal_id: str, **_: object) -> object:
        del session_id
        terminal = self._terminals[terminal_id]
        exit_status = None
        exit_code = terminal.proc.poll()
        if exit_code is not None:
            exit_status = _terminal_exit_status(self._schema, exit_code)
        return self._schema.TerminalOutputResponse(
            output=_read_text(terminal.output_path),
            truncated=False,
            exitStatus=exit_status,
        )

    def wait_for_terminal_exit(self, session_id: str, terminal_id: str, **_: object) -> object:
        del session_id
        terminal = self._terminals[terminal_id]
        exit_code = terminal.proc.wait()
        return _wait_response(self._schema, exit_code)

    def kill_terminal(self, session_id: str, terminal_id: str, **_: object) -> object:
        del session_id
        terminal = self._terminals[terminal_id]
        _terminate_popen(terminal.proc, 2.0)
        return self._schema.KillTerminalResponse()

    def release_terminal(self, session_id: str, terminal_id: str, **_: object) -> object:
        del session_id
        terminal = self._terminals.pop(terminal_id, None)
        if terminal is not None:
            _terminate_popen(terminal.proc, 0.5)
        return self._schema.ReleaseTerminalResponse()

    def cleanup(self) -> None:
        for terminal_id in list(self._terminals):
            self.kill_terminal("", terminal_id)
            self.release_terminal("", terminal_id)
        shutil.rmtree(self._tmpdir, ignore_errors=True)


class _Terminal:
    def __init__(self, *, proc: subprocess.Popen[bytes], output_path: Path) -> None:
        self.proc = proc
        self.output_path = output_path


def _to_acp_env(schema: object, env: dict[str, str] | None) -> list[object] | None:
    if env is None:
        return None
    return [schema.EnvVariable(name=name, value=value) for name, value in sorted(env.items())]


def _from_acp_env(env: list[object] | None) -> dict[str, str] | None:
    if env is None:
        return None
    return {item.name: item.value for item in env}


def _wait_response(schema: object, exit_code: int) -> object:
    if exit_code < 0:
        return schema.WaitForTerminalExitResponse(signal=_signal_name(-exit_code))
    return schema.WaitForTerminalExitResponse(exitCode=exit_code)


def _terminal_exit_status(schema: object, exit_code: int) -> object:
    if exit_code < 0:
        return schema.TerminalExitStatus(signal=_signal_name(-exit_code))
    return schema.TerminalExitStatus(exitCode=exit_code)


def _exit_code_from_acp(response: object) -> int | None:
    exit_code = getattr(response, "exit_code", None)
    if exit_code is not None:
        return int(exit_code)
    sig = getattr(response, "signal", None)
    if sig:
        return -_signal_number(sig)
    return None


def _exit_status_code(status: object | None) -> int | None:
    if status is None:
        return None
    return _exit_code_from_acp(status)


def _signal_name(number: int) -> str:
    try:
        return signal.Signals(number).name
    except ValueError:
        return f"SIG{number}"


def _signal_number(name: str) -> int:
    if name.startswith("SIG"):
        try:
            return int(name[3:])
        except ValueError:
            pass
    return int(getattr(signal, name, 0) or 0)


def _popen_session_kwargs() -> dict[str, object]:
    if os.name == "posix":
        return {"start_new_session": True}
    if os.name == "nt":
        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    return {}


def _terminate_popen(proc: subprocess.Popen[bytes], timeout_seconds: float) -> None:
    if proc.poll() is not None:
        return
    if os.name == "posix":
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
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
    else:
        proc.kill()
    try:
        proc.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        pass


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


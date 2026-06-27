from __future__ import annotations

import asyncio
import base64
import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import threading
import time
import uuid

from .models import AdapterCapabilities, BackgroundHandle, BackgroundStatus, CommandResult


class CodexAppServerAdapter:
    """Experimental adapter for Codex app-server `command/exec`.

    This runs direct app-server shell commands over stdio JSON-RPC. It does not
    create a model turn and does not ask Codex to reason about the command.
    """

    name = "codex-app-server"

    def __init__(self) -> None:
        if shutil.which("codex") is None:
            raise RuntimeError("codex CLI is not installed or not on PATH.")
        self.capabilities = AdapterCapabilities(
            name=self.name,
            supports_background=True,
            supports_env_override=True,
            supports_sticky_cwd=False,
        )
        self._rpc = _CodexAppServerRPC()
        self._background: dict[str, _CodexBackground] = {}

    async def run(
        self,
        command: str,
        *,
        cwd: Path,
        env: dict[str, str] | None = None,
        timeout_seconds: float = 10.0,
    ) -> CommandResult:
        start = time.monotonic()
        result = await asyncio.to_thread(
            self._rpc.request,
            "command/exec",
            {
                "command": _shell_argv(command),
                "cwd": str(cwd),
                "disableOutputCap": True,
                "env": _codex_env(env),
                "sandboxPolicy": {"type": "dangerFullAccess"},
                "timeoutMs": int(timeout_seconds * 1000),
            },
            max(timeout_seconds + 5.0, 10.0),
        )
        exit_code = int(result.get("exitCode", 0))
        return CommandResult(
            stdout=result.get("stdout", ""),
            stderr=result.get("stderr", ""),
            exit_code=exit_code,
            timed_out=exit_code == 124,
            duration_seconds=time.monotonic() - start,
            raw=json.dumps(result, sort_keys=True),
        )

    async def start_background(
        self,
        command: str,
        *,
        cwd: Path,
        env: dict[str, str] | None = None,
    ) -> BackgroundHandle:
        process_id = f"asc-{uuid.uuid4().hex}"
        request_id = self._rpc.send(
            "command/exec",
            {
                "command": _shell_argv(command),
                "cwd": str(cwd),
                "disableTimeout": True,
                "env": _codex_env(env),
                "processId": process_id,
                "sandboxPolicy": {"type": "dangerFullAccess"},
                "streamStdoutStderr": True,
            },
        )
        self._background[process_id] = _CodexBackground(request_id=request_id)
        return BackgroundHandle(id=process_id, command=command)

    async def check_background(self, handle: BackgroundHandle) -> BackgroundStatus:
        bg = self._background[handle.id]
        self._drain(handle.id, bg)
        response = self._rpc.response_nowait(bg.request_id)
        if response is not None:
            bg.response = response
        return BackgroundStatus(
            running=bg.response is None,
            stdout="".join(bg.stdout),
            stderr="".join(bg.stderr),
            exit_code=_response_exit_code(bg.response),
            raw=json.dumps(bg.response, sort_keys=True) if bg.response else "",
        )

    async def stop_background(self, handle: BackgroundHandle, *, timeout_seconds: float = 5.0) -> CommandResult:
        start = time.monotonic()
        bg = self._background.pop(handle.id)
        self._rpc.request("command/exec/terminate", {"processId": handle.id}, timeout_seconds)
        response = self._rpc.wait_response(bg.request_id, timeout_seconds)
        self._drain(handle.id, bg)
        if response is not None:
            bg.response = response
        return CommandResult(
            stdout="".join(bg.stdout),
            stderr="".join(bg.stderr),
            exit_code=_response_exit_code(bg.response),
            duration_seconds=time.monotonic() - start,
            raw=json.dumps(bg.response, sort_keys=True) if bg.response else "",
        )

    async def cleanup(self) -> None:
        for process_id, bg in list(self._background.items()):
            try:
                self._rpc.request("command/exec/terminate", {"processId": process_id}, 1.0)
                self._rpc.wait_response(bg.request_id, 1.0)
            except Exception:
                pass
        self._background.clear()
        await asyncio.to_thread(self._rpc.close)

    def _drain(self, process_id: str, bg: "_CodexBackground") -> None:
        for notification in self._rpc.notifications():
            if notification.get("method") != "command/exec/outputDelta":
                continue
            params = notification.get("params") or {}
            if params.get("processId") != process_id:
                self._rpc.keep_notification(notification)
                continue
            chunk = base64.b64decode(params.get("deltaBase64", "")).decode("utf-8", errors="replace")
            if params.get("stream") == "stderr":
                bg.stderr.append(chunk)
            else:
                bg.stdout.append(chunk)


class _CodexBackground:
    def __init__(self, *, request_id: int) -> None:
        self.request_id = request_id
        self.stdout: list[str] = []
        self.stderr: list[str] = []
        self.response: dict[str, object] | None = None


class _CodexAppServerRPC:
    def __init__(self) -> None:
        self._proc = subprocess.Popen(
            ["codex", "app-server", "--listen", "stdio://"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self._next_id = 0
        self._responses: dict[int, dict[str, object]] = {}
        self._notifications: queue.Queue[dict[str, object]] = queue.Queue()
        self._lock = threading.Lock()
        self._reader = threading.Thread(target=self._read_stdout, daemon=True)
        self._reader.start()
        self.request("initialize", {"clientInfo": {"name": "agent-shell-contract", "version": "0.1.0"}}, 5.0)

    def send(self, method: str, params: dict[str, object]) -> int:
        with self._lock:
            self._next_id += 1
            request_id = self._next_id
            message = {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}
            assert self._proc.stdin is not None
            self._proc.stdin.write(json.dumps(message) + "\n")
            self._proc.stdin.flush()
            return request_id

    def request(self, method: str, params: dict[str, object], timeout: float) -> dict[str, object]:
        request_id = self.send(method, params)
        response = self.wait_response(request_id, timeout)
        if response is None:
            raise TimeoutError(f"Timed out waiting for {method}")
        if "error" in response:
            raise RuntimeError(f"{method} failed: {response['error']}")
        result = response.get("result")
        return result if isinstance(result, dict) else {}

    def wait_response(self, request_id: int, timeout: float) -> dict[str, object] | None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            response = self.response_nowait(request_id)
            if response is not None:
                return response
            time.sleep(0.01)
        return None

    def response_nowait(self, request_id: int) -> dict[str, object] | None:
        return self._responses.pop(request_id, None)

    def notifications(self) -> list[dict[str, object]]:
        items: list[dict[str, object]] = []
        while True:
            try:
                items.append(self._notifications.get_nowait())
            except queue.Empty:
                return items

    def keep_notification(self, notification: dict[str, object]) -> None:
        self._notifications.put(notification)

    def close(self) -> None:
        if self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                self._proc.kill()
                self._proc.wait(timeout=2.0)

    def _read_stdout(self) -> None:
        assert self._proc.stdout is not None
        for line in self._proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "id" in message:
                self._responses[int(message["id"])] = message
            elif "method" in message:
                self._notifications.put(message)


def _shell_argv(command: str) -> list[str]:
    if os.name == "nt":
        return ["cmd", "/C", command]
    return ["/bin/sh", "-lc", command]


def _codex_env(env: dict[str, str] | None) -> dict[str, str | None] | None:
    if env is None:
        return None
    result: dict[str, str | None] = {name: None for name in os.environ if name not in env}
    result.update(env)
    return result


def _response_exit_code(response: dict[str, object] | None) -> int | None:
    if response is None:
        return None
    result = response.get("result")
    if not isinstance(result, dict):
        return None
    exit_code = result.get("exitCode")
    return int(exit_code) if exit_code is not None else None


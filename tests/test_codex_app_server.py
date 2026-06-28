from __future__ import annotations

import asyncio
from pathlib import Path
import unittest

from agent_shell_contract.codex_app_server import (
    CodexAppServerAdapter,
    CodexAppServerProtocolError,
    _decode_output_delta,
    _extract_result,
    _response_exit_code,
)


class _FakeRPC:
    def __init__(self, result: dict[str, object]) -> None:
        self.result = result

    def request(self, method: str, params: dict[str, object], timeout: float) -> dict[str, object]:
        return self.result


class CodexAppServerCompatibilityTests(unittest.TestCase):
    def test_json_rpc_error_reports_actionable_compatibility_context(self) -> None:
        with self.assertRaisesRegex(
            CodexAppServerProtocolError,
            r"command/exec.*JSON-RPC error.*codex --version.*method support",
        ):
            _extract_result(
                {"error": {"code": -32601, "message": "Method not found"}},
                "command/exec",
            )

    def test_non_object_result_reports_unsupported_shape(self) -> None:
        with self.assertRaisesRegex(
            CodexAppServerProtocolError,
            r"initialize.*unsupported result shape.*expected object.*got str",
        ):
            _extract_result({"result": "ready"}, "initialize")

    def test_run_rejects_missing_exec_fields(self) -> None:
        adapter = CodexAppServerAdapter.__new__(CodexAppServerAdapter)
        adapter._rpc = _FakeRPC({"stdout": "ok", "stderr": ""})

        async def run() -> None:
            await adapter.run("true", cwd=Path.cwd())

        with self.assertRaisesRegex(
            CodexAppServerProtocolError,
            r"command/exec.*integer field `exitCode`.*response schema",
        ):
            asyncio.run(run())

    def test_response_exit_code_rejects_invalid_type(self) -> None:
        with self.assertRaisesRegex(
            CodexAppServerProtocolError,
            r"command/exec.*integer field `exitCode`",
        ):
            _response_exit_code({"result": {"exitCode": "0"}})

    def test_output_delta_rejects_unknown_stream(self) -> None:
        notification = {
            "params": {
                "processId": "asc-1",
                "stream": "combined",
                "deltaBase64": "b2s=",
            }
        }
        with self.assertRaisesRegex(
            CodexAppServerProtocolError,
            r"outputDelta.*unsupported stream.*stdout.*stderr",
        ):
            _decode_output_delta(notification, "asc-1")

    def test_output_delta_decodes_matching_process(self) -> None:
        notification = {
            "params": {
                "processId": "asc-1",
                "stream": "stdout",
                "deltaBase64": "b2sK",
            }
        }
        self.assertEqual(_decode_output_delta(notification, "asc-1"), ("stdout", "ok\n"))

    def test_output_delta_keeps_other_process_notifications(self) -> None:
        notification = {
            "params": {
                "processId": "asc-other",
                "stream": "stdout",
                "deltaBase64": "b2sK",
            }
        }
        self.assertIsNone(_decode_output_delta(notification, "asc-1"))


if __name__ == "__main__":
    unittest.main()

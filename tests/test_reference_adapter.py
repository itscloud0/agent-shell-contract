from __future__ import annotations

import asyncio
import unittest
from unittest.mock import patch

from agent_shell_contract.adapters import ReferenceSubprocessAdapter, _terminate_windows_process_tree
from agent_shell_contract.models import FixtureStatus
from agent_shell_contract.runner import run_suite


class ReferenceAdapterTests(unittest.TestCase):
    def test_core_reference_fixtures_pass(self) -> None:
        async def run() -> list[FixtureStatus]:
            report = await run_suite(
                ReferenceSubprocessAdapter(),
                [
                    "timeout-child-pipe",
                    "timeout-process-tree",
                    "output-before-exit",
                    "output-after-kill",
                    "cwd-isolation",
                    "env-boundary",
                    "pty-detection",
                ],
            )
            return [result.status for result in report.results]

        statuses = asyncio.run(run())
        self.assertEqual(statuses, [FixtureStatus.PASS] * len(statuses))

    def test_background_reference_fixture_passes(self) -> None:
        async def run() -> FixtureStatus:
            report = await run_suite(ReferenceSubprocessAdapter(), ["background-server-lifecycle"])
            return report.results[0].status

        self.assertEqual(asyncio.run(run()), FixtureStatus.PASS)

    def test_windows_tree_termination_uses_taskkill_tree_mode(self) -> None:
        with patch("agent_shell_contract.adapters.subprocess.run") as run:
            _terminate_windows_process_tree(123)

        run.assert_called_once_with(
            ["taskkill", "/PID", "123", "/T", "/F"],
            capture_output=True,
            check=False,
            timeout=5.0,
        )


if __name__ == "__main__":
    unittest.main()

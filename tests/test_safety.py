from __future__ import annotations

import asyncio
import os
import unittest

from agent_shell_contract.adapters import ReferenceSubprocessAdapter
from agent_shell_contract.runner import run_suite


class SafetyTests(unittest.TestCase):
    def test_env_boundary_restores_existing_sentinel(self) -> None:
        os.environ["ASC_SENTINEL_SECRET"] = "original"

        async def run() -> None:
            await run_suite(ReferenceSubprocessAdapter(), ["env-boundary"])

        try:
            asyncio.run(run())
            self.assertEqual(os.environ.get("ASC_SENTINEL_SECRET"), "original")
        finally:
            os.environ.pop("ASC_SENTINEL_SECRET", None)

    def test_cleanup_runs_after_fixture_error(self) -> None:
        adapter = ReferenceSubprocessAdapter()

        async def run() -> None:
            await run_suite(adapter, ["windows-tree-termination"])

        asyncio.run(run())
        self.assertEqual(adapter._background, {})


if __name__ == "__main__":
    unittest.main()


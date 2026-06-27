from __future__ import annotations

import asyncio
import json
import unittest

from agent_shell_contract.adapters import ReferenceSubprocessAdapter
from agent_shell_contract.reports import render_json, render_markdown, render_terminal
from agent_shell_contract.runner import run_suite


class ReportTests(unittest.TestCase):
    def test_report_renderers_include_fixture_status(self) -> None:
        async def run():
            return await run_suite(ReferenceSubprocessAdapter(), ["output-before-exit"])

        report = asyncio.run(run())
        payload = json.loads(render_json(report))
        self.assertEqual(payload["results"][0]["fixture"], "output-before-exit")
        self.assertIn("PASS", render_terminal(report))
        self.assertIn("output-before-exit", render_markdown(report))


if __name__ == "__main__":
    unittest.main()


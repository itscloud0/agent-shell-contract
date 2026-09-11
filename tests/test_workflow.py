from __future__ import annotations

import re
import unittest
from pathlib import Path


class WorkflowTests(unittest.TestCase):
    def test_external_actions_use_reviewed_full_commit_pins(self) -> None:
        workflow = Path(__file__).parents[1] / ".github" / "workflows" / "ci.yml"
        refs = re.findall(r"^\s*- uses: (actions/[^\s]+)", workflow.read_text(), re.MULTILINE)

        self.assertEqual(
            refs,
            [
                "actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
                "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065",
                "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065",
                "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065",
                "actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
                "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065",
            ],
        )
        self.assertTrue(all(re.fullmatch(r"actions/[^@]+@[0-9a-f]{40}", ref) for ref in refs))

    def test_public_archive_install_is_pinned_and_checkout_free(self) -> None:
        root = Path(__file__).parents[1]
        workflow = (root / ".github" / "workflows" / "ci.yml").read_text()
        readme = (root / "README.md").read_text()
        archive_url = (
            "https://github.com/itscloud0/agent-shell-contract/archive/"
            "c018e00433d09a82c71a83d648d214d296b90f6b.tar.gz"
        )
        archive_job = workflow.split("  public-archive-install:", 1)[1].split(
            "  optional-adapters:", 1
        )[0]

        self.assertIn(archive_url, readme)
        self.assertEqual(archive_job.count(archive_url), 1)
        self.assertNotIn("actions/checkout@", archive_job)
        self.assertIn("agent-shell-contract run --adapter subprocess-reference", archive_job)


if __name__ == "__main__":
    unittest.main()

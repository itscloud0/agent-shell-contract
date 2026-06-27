from __future__ import annotations

import unittest

from agent_shell_contract.fixtures import fixture_names, select_fixtures


class FixtureSelectionTests(unittest.TestCase):
    def test_declares_expected_fixtures(self) -> None:
        names = fixture_names()
        self.assertIn("timeout-child-pipe", names)
        self.assertIn("background-server-lifecycle", names)
        self.assertIn("pty-detection", names)

    def test_unknown_fixture_fails(self) -> None:
        with self.assertRaises(ValueError):
            select_fixtures(["missing"])


if __name__ == "__main__":
    unittest.main()


from __future__ import annotations

import unittest
from unittest.mock import patch

from agent_shell_contract.fixtures import _py, fixture_names, select_fixtures


class FixtureSelectionTests(unittest.TestCase):
    def test_declares_expected_fixtures(self) -> None:
        names = fixture_names()
        self.assertIn("timeout-child-pipe", names)
        self.assertIn("background-server-lifecycle", names)
        self.assertIn("pty-detection", names)

    def test_unknown_fixture_fails(self) -> None:
        with self.assertRaises(ValueError):
            select_fixtures(["missing"])

    def test_windows_python_fixture_command_preserves_embedded_quotes(self) -> None:
        with patch("agent_shell_contract.fixtures.os.name", "nt"):
            command = _py('print("ASC_QUOTE_SAFE", flush=True)')

        self.assertIn("base64.b64decode", command)
        self.assertNotIn("ASC_QUOTE_SAFE", command)


if __name__ == "__main__":
    unittest.main()

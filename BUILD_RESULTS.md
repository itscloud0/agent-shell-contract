# Build Results: agent-shell-contract

## 2026-06-27 09:16 Europe/Amsterdam

Lifecycle mode: `BUILD`.

Built:

- Python package skeleton under `src/agent_shell_contract/`.
- Local CLI with `fixtures`, `run`, and `report` commands.
- Adapter protocol for shell runners.
- `subprocess-reference` adapter using stdlib subprocesses, owned process groups, temp dirs, and loopback ports.
- Optional `pydantic-ai-harness` adapter wrapper around Pydantic AI Harness `Shell`.
- Issue-derived fixture runner for timeout child pipes, process-tree timeout cleanup, background server lifecycle, output before exit, output after kill, cwd isolation, env boundary, PTY detection, and Windows tree termination.
- Terminal, JSON, and Markdown report rendering.
- Draft README with quickstart, adapter list, fixture list, and limitations.
- Unit/integration tests for fixture selection, reference adapter behavior, and report rendering.

Verification:

- `PYTHONPATH=src python3 -m unittest discover -s tests` passed: 5 tests.
- `PYTHONPATH=src python3 -m compileall -q src tests` passed.
- `PYTHONPATH=src python3 -m agent_shell_contract run --adapter subprocess-reference` passed: 8 `PASS`, 1 `SKIP` for Windows-only fixture.
- `PYTHONPATH=src python3 -m agent_shell_contract run --adapter subprocess-reference --fixture output-before-exit --json /tmp/asc-report.json --markdown /tmp/asc-report.md` passed.
- `PYTHONPATH=src python3 -m agent_shell_contract report --input /tmp/asc-report.json --format markdown` passed.
- `PYTHONPATH=src python3 -m agent_shell_contract run --adapter pydantic-ai-harness --fixture output-before-exit` returned the expected missing optional dependency message.

Gate impact:

- Minimal local build: `PASS`.
- Reference adapter fixture behavior: `PASS` on macOS with Windows-only fixture skipped.
- Pydantic AI Harness runtime validation: `UNKNOWN`; optional dependency is not installed locally.
- Benchmark, real-world validation, CI, discoverability, private publication, and public publication: `UNKNOWN`.

Exact next action:

Install or otherwise provide Pydantic AI Harness in an isolated environment, run the optional adapter against the fixture suite, then decide whether to continue to second-adapter validation or reposition upstream if the useful result is Pydantic-only.

## 2026-07-29 - Windows CI maintenance

- Added Windows tree termination with `taskkill /PID <pid> /T /F` and a Windows-safe encoded Python fixture command.
- Expanded CI to `windows-latest` for Python 3.10, 3.11, and 3.12.
- Corrective run `30435210271` passed all 9 matrix jobs plus the optional-adapter smoke job; owner issue #1 was closed.

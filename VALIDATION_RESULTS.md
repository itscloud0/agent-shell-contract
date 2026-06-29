# Validation Results: agent-shell-contract

## 2026-06-27 11:43 Europe/Amsterdam

Lifecycle mode: `VALIDATE`.

Target validation:

- Validate the optional Pydantic AI Harness adapter in an isolated dependency environment.
- Confirm whether the fixture runner produces meaningful contract results beyond the local subprocess reference adapter.
- Decide whether the project should continue toward a second stable adapter shape or be repositioned upstream as Pydantic-only.

Environment:

- Command: `uv run --python /opt/homebrew/bin/python3.12 --with pydantic-ai-harness --with-editable . python -m agent_shell_contract run --adapter pydantic-ai-harness --format json`
- Python: `3.12.11`
- Platform: `macOS-15.5-arm64-arm-64bit`
- Pydantic AI Harness package import succeeded from uv cache.
- `uv` created local `.venv` and `uv.lock`; both were removed after validation because they were incidental tool artifacts.

Result:

- `PASS`: 7
- `FAIL`: 1
- `SKIP`: 1
- `ERROR`: 0
- `UNSUPPORTED`: 0

Fixture outcomes:

- `timeout-child-pipe`: `PASS`; timeout returned without hanging on child pipes.
- `timeout-process-tree`: `PASS`; timeout terminated the owned process tree.
- `background-server-lifecycle`: `PASS`; background start/check/stop closed the owned port.
- `output-before-exit`: `PASS`; stdout, stderr, and exit status survived.
- `output-after-kill`: `FAIL`; timeout returned promptly but bounded pre-timeout stdout/stderr was not included in the timeout result.
- `cwd-isolation`: `PASS`; adapter declares sticky cwd support and behavior was recorded.
- `env-boundary`: `PASS`; explicit env boundary excluded the host sentinel variable.
- `pty-detection`: `PASS`; observed no-PTY behavior matched adapter declaration.
- `windows-tree-termination`: `SKIP`; Windows-only fixture skipped on macOS.

Gate impact:

- Pydantic AI Harness adapter feasibility: `PASS`.
- Meaningful external harness validation: `PASS`; the suite produced actionable pass/fail contract output against a real harness adapter.
- Specific Pydantic timeout-output contract: `FAIL`; timeout results drop bounded pre-kill output.
- Project-not-Pydantic-only decision: `PASS`; the runner has a reference adapter plus a working external harness adapter, and the failure is a reusable shell-semantics contract case rather than a Pydantic-specific unit test.
- Publication validation: `UNKNOWN`; still needs a second stable external adapter shape or a documented route showing ACP/native-client feasibility without UI automation or paid model calls.

Decision:

Continue incubation. Do not publish. Do not reposition upstream yet. The Pydantic result is useful validation, but publication still needs broader adapter evidence.

Exact next action:

Validate a second stable adapter shape. Prefer ACP terminal methods if a local implementation or conformance target can be run without UI automation; otherwise inspect Codex/Claude headless shell surfaces and kill or hand off if the remaining useful work is only a Pydantic AI Harness fixture contribution.

## 2026-06-27 12:20 Europe/Amsterdam

Lifecycle mode: `VALIDATE`.

Target validation:

- Validate a second adapter shape after the Pydantic AI Harness run.
- Prefer direct shell-runner APIs that do not require UI automation or paid model calls.

Adapters validated:

- `acp-local-terminal`: optional adapter using the official `agent-client-protocol` Python schema and ACP v1 terminal method names with a local in-process terminal client.
- `codex-app-server`: experimental adapter over Codex CLI `app-server` `command/exec`, using direct JSON-RPC shell execution without model calls.

Environment:

- ACP command: `uv run --python /opt/homebrew/bin/python3.12 --with agent-client-protocol --with-editable . python -m agent_shell_contract run --adapter acp-local-terminal --json reports/acp-local-terminal.json --markdown reports/acp-local-terminal.md`
- Codex command: `PYTHONPATH=src python3 -m agent_shell_contract run --adapter codex-app-server --json reports/codex-app-server.json --markdown reports/codex-app-server.md`
- Codex version: `codex-cli 0.133.0`
- Codex app-server methods tested: `initialize`, `command/exec`, `command/exec/outputDelta`, and `command/exec/terminate`.
- Platform: `macOS-15.5-arm64-arm-64bit`

Results:

| Adapter | PASS | FAIL | SKIP | Notes |
|---|---:|---:|---:|---|
| `subprocess-reference` | 8 | 0 | 1 | Baseline local adapter. |
| `pydantic-ai-harness` | 7 | 1 | 1 | `output-after-kill` drops bounded pre-timeout output. |
| `acp-local-terminal` | 8 | 0 | 1 | Protocol-shape validation, not a specific ACP product claim. |
| `codex-app-server` | 8 | 0 | 1 | Real local Codex shell surface, but app-server is experimental. |

Saved reports:

- `reports/subprocess-reference.json`
- `reports/subprocess-reference.md`
- `reports/pydantic-ai-harness.json`
- `reports/pydantic-ai-harness.md`
- `reports/acp-local-terminal.json`
- `reports/acp-local-terminal.md`
- `reports/codex-app-server.json`
- `reports/codex-app-server.md`

Gate impact:

- Second adapter validation: `PASS`, narrowly. Codex app-server is a real local direct shell surface that ran the full suite without model calls; ACP local validates a protocol-shaped adapter. Caveat: Codex app-server is experimental and ACP local is not a pass claim for a specific ACP client.
- Real-world cases: `PASS` for fixture classes mapped to Codex timeout/output/process issues, Claude/Pydantic background lifecycle issues, and Copilot/terminal output/cwd pain in the demand evidence.
- Publication validation: `PASS` for public release readiness after CI/docs/safety/discoverability checks and final GitHub Actions verification.

Decision:

Continue to public publication after the final release-candidate CI run passes.

## 2026-06-28 21:28 Europe/Amsterdam

Lifecycle mode: `MAINTAIN`.

Target validation:

- Harden the experimental Codex app-server adapter against schema/version drift.
- Keep the compatibility claim bounded to the local Codex CLI version and methods tested.

Environment:

- Codex version: `codex-cli 0.133.0`
- Codex app-server methods tested: `initialize`, `command/exec`, `command/exec/outputDelta`, and `command/exec/terminate`.
- Live command: `PYTHONPATH=src python3 -m agent_shell_contract run --adapter codex-app-server --format json`
- Platform: `macOS-15.5-arm64-arm-64bit`

Result:

- `PASS`: 8
- `SKIP`: 1
- `FAIL`: 0
- `ERROR`: 0

Gate impact:

- Codex app-server compatibility guard: `PASS`; the adapter reports JSON-RPC errors, non-object results, missing or mistyped `exitCode` / `stdout` / `stderr`, and malformed output-delta notifications as method-specific compatibility errors instead of silently accepting mismatched response shapes.
- Stable Codex API support claim: `FAIL`; app-server remains experimental and version-sensitive.

Decision:

Continue maintaining `codex-app-server` as experimental validation evidence only. Do not claim stable Codex API compatibility.

## 2026-06-29 17:58 Europe/Amsterdam

Lifecycle mode: `MAINTAIN`.

Target validation:

- Reproduce the Pydantic AI Harness `output-after-kill` contract failure from owner-created issue #2.
- Produce a minimal upstream-ready report without claiming maintainer interest or doing external upstream work from the OWNED lane.

Environment:

- Command: `uv run --python /opt/homebrew/bin/python3.12 --with pydantic-ai-harness --with-editable . python -m agent_shell_contract run --adapter pydantic-ai-harness --fixture output-after-kill --json reports/pydantic-ai-harness-output-after-kill.json --markdown reports/pydantic-ai-harness-output-after-kill.md`
- Pydantic AI Harness version: `0.4.0`
- Python: `3.12.11`
- Platform: `macOS-15.5-arm64-arm-64bit`

Result:

- `FAIL`: 1
- Fixture: `output-after-kill`
- Observed result: timeout returned promptly, but `stdout` and `stderr` were empty and raw output was only `[Command timed out after 1.0s]`.

Saved reports:

- `reports/pydantic-ai-harness-output-after-kill.json`
- `reports/pydantic-ai-harness-output-after-kill.md`
- `reports/pydantic-ai-harness-output-after-kill-report.md`

Decision:

Keep the report local and upstream-ready. Do not open a Pydantic AI Harness upstream issue from this OWNED-lane run; a separate UPSTREAM run should first check that repository's contribution rules and current behavior.

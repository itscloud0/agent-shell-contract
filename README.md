# agent-shell-contract

`agent-shell-contract` is a local shell semantics contract suite for coding-agent client authors, agent harness maintainers, and advanced users debugging hung agent commands, leaked dev servers, lost terminal output, cwd drift, environment leakage, and process-tree cleanup failures.

It runs issue-derived fixtures against a shell-runner adapter and emits concise terminal, JSON, and Markdown reports that can be attached to upstream bug reports.

## Quickstart

Install from a local checkout:

```bash
python3 -m pip install -e .
```

Run every fixture against the subprocess reference adapter:

```bash
agent-shell-contract run --adapter subprocess-reference
```

Run one fixture and write reports:

```bash
PYTHONPATH=src python3 -m agent_shell_contract run \
  --adapter subprocess-reference \
  --fixture timeout-process-tree \
  --json report.json \
  --markdown report.md
```

List available coding-agent shell timeout, background process cleanup, terminal output, cwd isolation, env boundary, and PTY fixtures:

```bash
PYTHONPATH=src python3 -m agent_shell_contract fixtures
```

Optional Pydantic AI Harness adapter:

```bash
python3 -m pip install ".[pydantic-ai-harness]"
agent-shell-contract run --adapter pydantic-ai-harness
```

Optional ACP local terminal adapter:

```bash
python3 -m pip install ".[acp]"
agent-shell-contract run --adapter acp-local-terminal
```

Experimental Codex app-server adapter, when `codex app-server` is installed:

```bash
agent-shell-contract run --adapter codex-app-server
```

This adapter targets the experimental Codex CLI app-server JSON-RPC surface. It reports actionable compatibility errors when response shapes drift; it is not a stable Codex API support claim.

## Included Fixtures

- `timeout-child-pipe`: timeout must not hang when a child keeps stdout or stderr open.
- `timeout-process-tree`: timeout should terminate the owned process tree.
- `background-server-lifecycle`: background start/check/stop should close the owned local port.
- `output-before-exit`: stdout, stderr, and non-zero exit status must survive normal completion.
- `output-after-kill`: bounded useful output should remain available after timeout or kill.
- `cwd-isolation`: `cd` in one command must not silently mutate later commands unless declared sticky.
- `env-boundary`: explicit env mode should keep host sentinel variables out of the child.
- `pty-detection`: PTY behavior should be observable and match adapter declaration.
- `windows-tree-termination`: Windows-specific process-tree termination, skipped elsewhere.

## Adapters

- `subprocess-reference`: stdlib baseline using owned temporary directories, process groups, pipes, and local ports.
- `pydantic-ai-harness`: optional wrapper over Pydantic AI Harness `Shell`; useful for validating a current framework shell implementation without model calls.
- `acp-local-terminal`: optional adapter using the official `agent-client-protocol` Python schema and ACP terminal method names with a local terminal client. It validates ACP adapter shape without UI automation or model calls; it is not a pass claim for a specific ACP client.
- `codex-app-server`: experimental adapter over Codex CLI app-server `command/exec`. It runs direct shell commands without model calls, but the app-server surface is experimental and version-sensitive.

See `ADAPTERS.md` for adapter authoring notes and result interpretation.

## Known Validation Results

| Adapter | Result | Notes |
|---|---:|---|
| `subprocess-reference` | 8 pass, 1 skip | Windows-only fixture skipped on macOS. |
| `pydantic-ai-harness` | 7 pass, 1 fail, 1 skip | `output-after-kill` drops bounded pre-timeout output. |
| `acp-local-terminal` | 8 pass, 1 skip | Validates ACP terminal method shape with a local terminal client. |
| `codex-app-server` | 8 pass, 1 skip | Experimental Codex CLI direct shell surface; Windows-only fixture skipped on macOS. |

Raw JSON and Markdown reports are stored under `reports/` when generated during validation.

## Comparison

- Bats, ShellSpec, pexpect, and pytest process helpers can test shell behavior, but they do not define a coding-agent shell adapter contract.
- Agent task benchmarks such as Terminal-Bench test end-to-end task success, not low-level shell timeout, output, cwd, env, PTY, and process-tree semantics.
- Process managers help operate long-running jobs; this suite reports whether an existing shell runner honors issue-derived contracts.

## Limitations

This is not a process manager, sandbox, security scanner, model benchmark, or automatic fix for Codex, Claude Code, Copilot, or ACP clients. Fixtures only create owned temporary files, owned local child processes, and loopback ports. Results can vary by OS process semantics; unsupported platform behavior is reported explicitly.

Windows process-tree behavior is not validated yet. The ACP adapter validates a protocol-shaped local terminal client, not a specific ACP product implementation. The Codex app-server adapter depends on an experimental Codex CLI API and may need updates when Codex app-server methods or response schemas change.

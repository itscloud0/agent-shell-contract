# agent-shell-contract v0.1.0

Initial private incubation release candidate for `agent-shell-contract`.

## Included

- Local CLI for coding-agent shell-runner contract fixtures.
- Reference subprocess adapter.
- Optional Pydantic AI Harness adapter.
- Optional ACP local terminal adapter using official `agent-client-protocol` schema models.
- Experimental Codex app-server adapter for direct `command/exec` shell validation without model calls.
- Nine issue-derived fixtures covering timeout behavior, process-tree cleanup, background server lifecycle, output preservation, cwd isolation, env boundary, PTY declaration, and Windows termination.
- Terminal, JSON, and Markdown reports.
- Safety, discoverability, validation, and benchmark documentation.

## Known Findings

- Pydantic AI Harness validation produced an actionable `output-after-kill` failure: timeout returns promptly but does not include bounded pre-timeout stdout/stderr in the timeout result.
- Codex app-server validation passed 8 non-Windows fixtures locally on Codex CLI `0.133.0`; app-server remains experimental.
- ACP local terminal validation passed 8 non-Windows fixtures locally using the official Python schema package; this validates adapter shape, not a specific ACP client product.
- Windows process-tree behavior is not validated in CI yet.
- Codex app-server validation depends on an experimental local Codex CLI API.

## Limitations

This is not a process manager, sandbox, model benchmark, or automatic fixer. The ACP adapter validates protocol shape with a local terminal client; it is not a pass claim for a specific ACP client.

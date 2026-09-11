# agent-shell-contract v0.2.0

This release packages the verified Windows reference-adapter support added after the initial public release.

## Post-release maintenance

- Added a checkout-free install path from the immutable `v0.2.0` source archive for users without Git or PyPI access.
- Added a no-checkout GitHub Actions smoke test and regression coverage so the documented archive stays pinned to the released commit.
- This maintenance update does not change the `v0.2.0` package version or release tag.

## Included

- Windows process-tree termination through `taskkill /PID <pid> /T /F` for the reference adapter.
- Windows-safe encoded fixture commands that preserve embedded quotes.
- `windows-latest` CI coverage for Python 3.10, 3.11, and 3.12, with all nine reference fixtures passing.
- Actionable compatibility errors and bounded documentation for the experimental Codex app-server adapter.

## Validation

- Corrective Windows matrix run `30435210271`: all nine matrix jobs passed.
- Optional-adapter smoke run `30435595844`: passed.
- This release's package version is `0.2.0`; the Windows claim remains limited to the reference adapter and tested GitHub Actions runners.

## Limitations

The Codex app-server adapter remains experimental and version-sensitive. Windows behavior is not claimed for other adapters or client products.

# agent-shell-contract v0.1.0

Initial public release of `agent-shell-contract`.

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
- Windows process-tree behavior is covered by the reference adapter in CI run `30435210271` across Python 3.10, 3.11, and 3.12 on `windows-latest`.
- Codex app-server validation depends on an experimental local Codex CLI API.

## Limitations

This is not a process manager, sandbox, model benchmark, or automatic fixer. The ACP adapter validates protocol shape with a local terminal client; it is not a pass claim for a specific ACP client.

# Adapter Guide

Adapters implement a small shell-runner protocol:

- `run(command, cwd, env, timeout_seconds)`
- `start_background(command, cwd, env)`
- `check_background(handle)`
- `stop_background(handle, timeout_seconds)`
- `cleanup()`

Each adapter declares capabilities:

- PTY allocation: `True`, `False`, or `None` if unknown.
- Background command support.
- Explicit environment override support.
- Sticky cwd support.

## Built-In Adapters

### `subprocess-reference`

Local standard-library baseline. It uses process groups on POSIX and owned temporary files for background output. It is not an agent client.

### `pydantic-ai-harness`

Optional adapter over Pydantic AI Harness `Shell`. It validates a real framework shell implementation without model calls.

Install:

```bash
python -m pip install ".[pydantic-ai-harness]"
```

### `acp-local-terminal`

Optional adapter that uses the official `agent-client-protocol` Python schema and ACP terminal method names with a local in-process terminal client.

It validates the ACP terminal adapter shape without UI automation or paid model calls. It does not claim that any specific ACP client implementation has passed.

Install:

```bash
python -m pip install ".[acp]"
```

### `codex-app-server`

Experimental adapter over Codex CLI `app-server` `command/exec`.

It uses direct JSON-RPC shell execution and does not create a model turn. The Codex app-server API is experimental, so results should be treated as local validation evidence, not a stable public compatibility claim.

Validated locally with Codex CLI `0.133.0`: 8 fixtures passed and the Windows-only fixture skipped on macOS. The validation exercised these app-server surfaces:

- `initialize`
- `command/exec`
- `command/exec/outputDelta` notifications for background stdout/stderr
- `command/exec/terminate`

The adapter intentionally fails closed when Codex app-server responses do not match the tested shape. Unsupported JSON-RPC errors, non-object results, missing or incorrectly typed `exitCode` / `stdout` / `stderr`, and malformed output-delta notifications are reported with compatibility errors that name the method and ask the user to verify `codex --version`.

## Result Interpretation

- `PASS`: the adapter honored the fixture contract on the current platform.
- `FAIL`: the adapter violated the contract.
- `UNSUPPORTED`: the adapter does not claim the required capability.
- `SKIP`: the fixture is not applicable on the current platform.
- `ERROR`: the fixture or adapter crashed before producing a contract verdict.

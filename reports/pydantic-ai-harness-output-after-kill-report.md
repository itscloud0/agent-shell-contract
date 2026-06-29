# Pydantic AI Harness `output-after-kill` Contract Report

Status: local upstream-ready report, not filed upstream from this OWNED-lane run.

## Reproduction

Repository checkout:

```bash
uv run --python /opt/homebrew/bin/python3.12 \
  --with pydantic-ai-harness \
  --with-editable . \
  python -m agent_shell_contract run \
  --adapter pydantic-ai-harness \
  --fixture output-after-kill \
  --json reports/pydantic-ai-harness-output-after-kill.json \
  --markdown reports/pydantic-ai-harness-output-after-kill.md
```

Environment:

- `agent-shell-contract`: local checkout, version `0.1.0`
- `pydantic-ai-harness`: `0.4.0`
- Python: `3.12.11`
- Platform: `macOS-15.5-arm64-arm-64bit`
- Run timestamp: `2026-06-29T15:58:00Z`

The command exits non-zero because the fixture records a contract failure.

## Fixture

The fixture starts a Python command that writes and flushes stdout and stderr markers, then sleeps past the adapter timeout:

```python
import sys
import time
print("ASC_STDOUT_BEFORE_KILL", flush=True)
print("ASC_STDERR_BEFORE_KILL", file=sys.stderr, flush=True)
time.sleep(10)
```

The adapter runs it with `timeout_seconds=1.0`.

## Expected Contract

When a foreground command times out after producing bounded flushed output, the timeout result should:

- return promptly with `timed_out=True`
- preserve available pre-timeout stdout and stderr in the command result
- include at least one of `ASC_STDOUT_BEFORE_KILL` or `ASC_STDERR_BEFORE_KILL` in the captured output

This matters for coding-agent shell runners because timeout output often contains the actionable build, test, server, or diagnostic line needed to debug the failure.

## Observed Behavior

`pydantic-ai-harness` returns promptly and marks the command as timed out, but the timeout result drops the flushed pre-timeout output:

```json
{
  "exit_code": null,
  "raw": "[Command timed out after 1.0s]",
  "stderr": "",
  "stdout": "",
  "timed_out": true
}
```

`agent-shell-contract` records this as:

```text
FAIL        output-after-kill: bounded pre-kill output was lost
```

Full scoped artifacts:

- `reports/pydantic-ai-harness-output-after-kill.json`
- `reports/pydantic-ai-harness-output-after-kill.md`

## Upstream Action Decision

Do not claim Pydantic AI Harness maintainer interest yet. This report remains local because this run is scoped to Ilia-owned repository maintenance and must not perform external upstream contribution work. If selected by the UPSTREAM lane later, first check the Pydantic AI Harness repository contribution rules and current timeout-output behavior, then use this report as the issue or fixture proposal basis.

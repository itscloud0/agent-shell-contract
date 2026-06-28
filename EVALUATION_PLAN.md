# Evaluation Plan: agent-shell-contract

## Central Claim

`agent-shell-contract` should make coding-agent shell-runner bugs reproducible faster than manual `ps`/`lsof`/ad hoc shell scripts by running a deterministic fixture suite against a client or harness adapter and emitting an upstream-ready report.

## Primary Evaluation

Build the fixture runner and validate it against:

- a local subprocess reference adapter
- Pydantic AI Harness `Shell`
- one second external adapter shape before publication, preferably ACP terminal methods or another open harness with stable process APIs

Publication must not happen if only the subprocess reference adapter works.

## Fixture Matrix

| Fixture | Public pain mapped | Expected contract |
|---|---|---|
| `timeout-child-pipe` | Codex timeout hangs with child stdout/stderr pipes | timeout returns bounded result and does not hang on inherited pipes |
| `timeout-process-tree` | Codex/Claude child process leaks | timeout terminates the owned process tree or reports unsupported semantics |
| `background-server-lifecycle` | Claude/Copilot long-running dev-server failures | start/check/stop lifecycle works and the test port closes |
| `output-before-exit` | Copilot terminal output not received | stdout, stderr, and exit status survive normal completion |
| `output-after-kill` | timeout/kill loses final useful output | bounded final output is available after timeout or kill when supported |
| `cwd-isolation` | Copilot/VS Code cwd confusion | cwd behavior is stable and declared: isolated by default or sticky by configuration |
| `env-boundary` | shell subprocess inherits unexpected host env | explicit env mode prevents sentinel variables from reaching child |
| `pty-detection` | Codex no-TTY execution surprises | PTY allocation is observable and accurately declared |
| `windows-tree-termination` | Claude Windows background process remains alive | Windows adapter either terminates process tree or marks unsupported |

## Baselines

Manual baseline:

```bash
ps -ef
lsof -iTCP -sTCP:LISTEN -n -P
kill <pid>
pkill -P <pid>
python3 repro.py
```

Tooling baseline:

- Bats or ShellSpec for plain shell tests.
- pexpect or pytest process helpers for custom process assertions.
- Pydantic AI Harness native tests when validating the Pydantic adapter.

The contract suite must add value over these baselines by packaging the agent/harness adapter layer and issue-derived reports.

## Metrics

Detection:

- number of public pain classes represented by fixtures
- pass/fail/unsupported result clarity per adapter
- false failures caused by expected platform differences

Cleanup:

- zero fixture-owned child processes left alive after each test
- zero fixture-owned listening ports left open after each test
- bounded fixture runtime with explicit timeout failures

Workflow:

- commands replaced compared with manual repro
- time to produce an upstream-ready markdown report
- ability to rerun one fixture by name

Engineering:

- unit tests for fixture definitions, adapter protocol, process probes, and report rendering
- integration tests for reference adapter
- CI on Linux and macOS
- Windows fixture documented as unsupported or tested in CI

## Real-World Validation Cases

Before publication, model at least three unrelated public cases:

- Codex timeout and child-process pipe hang from issues #4337 or #5229.
- Claude Code background-process/session-exit cleanup from issues #43944 or #25180.
- Copilot/VS Code terminal output or long-running server/cwd handling from GitHub Community #161238 or VS Code #288890.

At least two ecosystems must be represented. Pydantic AI Harness counts as a framework/harness ecosystem; ACP or a native coding-agent client counts as the second only if the adapter is stable enough to run without UI automation.

## Safety Checks

- Fixtures create only owned temporary directories, processes, and local ports.
- Fixtures do not kill by broad name pattern.
- Fixtures do not send destructive shell commands.
- Fixtures do not read `.env`, secrets, or unrelated project files.
- Fixture reports redact absolute temp paths if they are not useful for reproduction.

## Discoverability Gate

Status: `PASS`.

Verified before public publication:

- README title and first paragraph state the exact problem: coding-agent shell timeout, background process cleanup, terminal output, and process-tree semantics.
- Package metadata and repository topics include accurate terms such as `coding-agent`, `shell`, `terminal`, `process-cleanup`, `conformance`, and `developer-tools`.
- Quickstart includes the phrases developers search when debugging hung agent commands or leaked dev servers.
- Limitations state unsupported clients and platform differences plainly.
- Distribution plan names concrete issue threads, ACP/Pydantic/benchmark communities, and package search surfaces without implying adoption.

## Stop Or Reposition Criteria

Stop or reposition if:

- the Pydantic adapter is the only realistic adapter
- ACP terminal methods already grow an equivalent fixture suite before this project has standalone value
- fixture results are too platform-dependent to interpret
- basic validation requires paid model calls or fragile UI automation
- the product becomes another background process manager
- upstream maintainers clearly prefer direct fixture contributions and there is no reusable owned surface left

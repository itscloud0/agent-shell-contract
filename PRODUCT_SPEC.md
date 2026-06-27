# PRODUCT_SPEC: agent-shell-contract

## User Persona

Coding-agent client authors, agent harness maintainers, and advanced users who need shell-command tools to behave predictably across Codex, Claude Code, Copilot/VS Code agent mode, ACP clients, and framework harnesses.

## Painful Problem

Coding agents repeatedly mishandle shell-command semantics: timeouts kill the wrong process, child processes survive after timeout or session exit, background servers keep running, terminal output is lost, working directories drift, PTY assumptions break commands, and Windows process termination differs from Unix process groups.

Each bug currently gets a one-off reproduction. There is no small, issue-derived contract suite that says what a coding-agent shell runner must preserve and then runs that contract against a client or harness adapter.

## Current Bad Workflow

1. Hit a hung command, runaway dev server, missing terminal output, or killed session.
2. Manually inspect `ps`, `lsof`, logs, IDE terminals, and agent transcripts.
3. Create a client-specific GitHub issue with a fragile repro.
4. Wait for each upstream to rediscover timeout, output, process-tree, and background-job edge cases independently.
5. Repeat the same bug class in the next agent or harness.

## Proposed Better Workflow

Run an issue-derived shell semantics suite:

```bash
agent-shell-contract run --adapter pydantic-ai-harness
agent-shell-contract run --adapter subprocess-reference --fixture timeout-child-pipe
agent-shell-contract report --format markdown
```

The tool runs deterministic shell fixtures through an adapter and reports whether the adapter preserves the contract:

- command completion and exit status
- stdout/stderr delivery before exit, after timeout, and after kill
- timeout behavior that terminates the command tree, not the agent host
- background start/check/stop lifecycle
- process-tree cleanup after run end
- cwd isolation or explicitly declared sticky cwd
- explicit environment boundary behavior
- PTY versus non-PTY behavior
- platform-specific termination behavior, including Windows skips or failures

## Core v0.1 Feature Set

- Local CLI only. No hosted service.
- Fixture runner with deterministic commands and per-platform expectations.
- Minimal adapter protocol for shell runners: run, start background, check output, stop/kill, cleanup.
- Built-in reference adapter using local subprocess primitives as a baseline.
- One natural framework adapter, initially Pydantic AI Harness `Shell`, because it is a current open-source shell implementation with foreground and background command support.
- JSON report and concise terminal report.
- Markdown issue-reproduction report for upstream bug filing.
- Safety checks for leftover child processes and occupied ports created by fixtures.
- Documentation of unsupported clients, OS limits, and known false positives.

## Candidate Fixtures

- `timeout-child-pipe`: command spawns a child that keeps stdout/stderr open after the parent exits or is killed.
- `timeout-process-tree`: timeout must terminate the whole process group or equivalent tree.
- `background-server-lifecycle`: start a local server, observe output, stop it, and verify the port closes.
- `output-before-exit`: adapter must deliver stdout/stderr and non-zero exit status without losing final lines.
- `output-after-kill`: timeout or kill result must include bounded final output when available.
- `cwd-isolation`: `cd` in one command must not silently affect later commands unless sticky cwd is declared.
- `env-boundary`: explicit env mode must prevent inherited sentinel variables from reaching the child.
- `pty-detection`: fixture records whether a PTY was allocated and fails only when the adapter misdeclares behavior.
- `windows-tree-termination`: Windows-specific process-tree termination fixture, skipped on non-Windows hosts.

## Non-Goals

- No new process manager.
- No replacement shell runner.
- No agent UI automation as a required v0.1 adapter.
- No broad LLM benchmark or leaderboard.
- No model prompting benchmark.
- No security sandbox guarantee.
- No automatic fixes for Codex, Claude Code, Copilot, or framework internals.
- No fake adoption metrics or claimed upstream interest.

## Existing Tools And Why This Is Different

- AttractorBench and Terminal-Bench evaluate whether agents complete broader coding or terminal tasks. `agent-shell-contract` tests low-level shell-runner semantics directly.
- Pydantic AI Harness `Shell` implements a framework-specific shell capability with foreground commands, background commands, timeouts, env controls, cwd handling, and process-group cleanup. `agent-shell-contract` can validate that implementation and others with reusable fixtures.
- ACP defines terminal protocol methods such as create, output, wait, kill, and release. It does not by itself provide an OS/process-semantics fixture corpus for adapters.
- `gob` helps humans and agents manage jobs. It is an operational process manager, not a conformance suite.
- `cc-reaper` cleans orphaned Claude/Codex-related processes. It is a cleanup tool, not a shell-runner contract.
- Bats, ShellSpec, pexpect, and pytest process tools can test shell behavior, but they do not define a coding-agent shell adapter contract.

## Why Upstream Contribution Is Insufficient

The bugs are client-specific and still need upstream fixes, but the failure pattern spans multiple clients and harnesses. A shared fixture corpus can turn repeated one-off reports into reproducible, comparable contract failures.

ACP, Pydantic AI Harness, AttractorBench, Terminal-Bench, or individual clients may later absorb specific fixtures. The standalone incubation is justified only if the first build proves the fixture suite is reusable across at least two adapter shapes and does not collapse into a Pydantic-only test plugin.

## Why This Strengthens Ilia's Profile

This is systems-oriented AI developer infrastructure: process control, terminal semantics, cross-platform edge cases, reproducible fixtures, and measurable conformance for coding-agent reliability. It is not a prompt wrapper or generic dashboard.

## Publish Criteria

- Demand, product, validation, usability, engineering, distribution, and discoverability gates are recorded as `PASS`, `FAIL`, or `UNKNOWN`.
- At least three unrelated public failure cases are modeled by fixtures.
- At least two ecosystems are validated when practical, with Pydantic AI Harness plus one ACP/client/harness adapter as the first target.
- A meaningful baseline compares the contract suite against manual `ps`/`lsof`/ad hoc shell repros and generic shell test frameworks.
- Tests prove fixtures clean up their own processes and ports.
- CI runs on Linux and macOS; Windows support is either tested or clearly marked experimental.
- README states the exact developer pain, target user, limitations, supported adapters, and search terms naturally.
- No private tokens, `.env` reads, destructive commands, public-network scans, or broad process killing outside fixture-owned process trees.

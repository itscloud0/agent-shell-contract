# Demand Evidence: agent-shell-contract

## Gate Summary

- Repeated public pain: `PASS`.
- Independent sources: `PASS`.
- Current workarounds reviewed: `PASS`.
- Existing tools reviewed: `PASS`.
- Clear standalone gap: `PASS`, narrowly for an issue-derived shell-command contract suite, not a process manager.
- Upstream-insufficiency: `PASS`, narrowly. Client fixes belong upstream, but a shared fixture corpus spans multiple upstreams.
- Credible distribution path: `PASS`, through affected client/harness issue threads, ACP implementers, Pydantic AI Harness, and agent benchmark/tooling communities. No traction claimed.
- Measurable success criteria: `PASS`.
- Discoverability gate: `PASS`; README, package metadata, repository metadata, release notes, limitations, and distribution plan now exist without adoption or traction claims.

## Public Pain Signals

- OpenAI Codex issue #4337 reports commands hanging after timeout because only the shell is killed while child processes keep stdout/stderr pipes open. Source: https://github.com/openai/codex/issues/4337
- OpenAI Codex issue #5229 reports `timeout_ms` not terminating child processes such as `next dev`, causing command calls to hang indefinitely. Source: https://github.com/openai/codex/issues/5229
- OpenAI Codex issue #15379 reports orphaned child processes after the Codex parent process exits. Source: https://github.com/openai/codex/issues/15379
- OpenAI Codex issue #15596 reports timeouts while waiting for child processes to exit. Source: https://github.com/openai/codex/issues/15596
- OpenAI Codex issue #19945 reports `codex exec` running without a TTY and detaching without useful terminal feedback. Source: https://github.com/openai/codex/issues/19945
- Anthropic Claude Code issue #45717 reports Bash tool timeout behavior where `SIGTERM` kills Claude Code itself instead of only the timed-out shell command. Source: https://github.com/anthropics/claude-code/issues/45717
- Anthropic Claude Code issue #43944 reports background processes not being cleaned up on session exit, including runaway `next dev` servers. Source: https://github.com/anthropics/claude-code/issues/43944
- Anthropic Claude Code issue #25180 reports spawned subprocesses recurring and exhausting system resources, with proposed fixes around process groups, PID tracking, cleanup handlers, and watchdogs. Source: https://github.com/anthropics/claude-code/issues/25180
- Anthropic Claude Code issue #8865 reports Windows background tasks marked killed in the UI while the actual OS process remains alive. Source: https://github.com/anthropics/claude-code/issues/8865
- GitHub Community discussion #170008 reports Copilot agent mode reusing and killing a long-lived server terminal despite user instructions. Source: https://github.com/orgs/community/discussions/170008
- VS Code issue #288890 reports Copilot Agent mishandling long-running Spring Boot server terminals and working-directory/server lifecycle. Source: https://github.com/microsoft/vscode/issues/288890
- GitHub Community discussion #161238 reports Copilot agent failing to receive terminal output from commands. Source: https://github.com/orgs/community/discussions/161238
- Pydantic AI Harness issue #60 requests background process management for coding agents and cites a spawn/list/get/kill/sendStdin/wait style ProcessManager. Source: https://github.com/pydantic/pydantic-ai-harness/issues/60

## Current Workarounds

- Manual `ps`, `lsof`, `kill`, `pkill`, shell job control, PID files, port-kill scripts, terminal tabs, tmux, and agent restarts.
- Client-native controls such as Codex `/ps` and `/stop`, Claude Code background Bash controls, and IDE terminal management.
- Operational tools such as `gob` for shared agent/human job management and `cc-reaper` for orphan cleanup.
- Framework-level shell tools such as Pydantic AI Harness `Shell`.
- General shell testing libraries such as Bats, ShellSpec, pexpect, and pytest process helpers.

## Targeted Validation: Existing Tools

### AttractorBench

Source: https://github.com/strongdm/attractorbench

AttractorBench measures whether coding agents implement systems from natural-language specifications. It includes a coding-agent-loop tier with shell and file tools, but the benchmark target is end-to-end spec conformance, not low-level shell-runner semantics such as process-tree timeout cleanup, output drains after kill, PTY declaration, or Windows termination behavior.

Gate impact: standalone gap remains `PASS`.

### Terminal-Bench

Source: https://github.com/harbor-framework/terminal-bench

Terminal-Bench evaluates agents on real terminal tasks in sandboxed environments. It is useful adjacent infrastructure, but it is task-oriented and leaderboard-oriented. It does not define a small adapter contract for shell-runner process semantics.

Gate impact: standalone gap remains `PASS`.

### Pydantic AI Harness Shell

Sources:

- https://github.com/pydantic/pydantic-ai-harness
- https://github.com/pydantic/pydantic-ai-harness/issues/60

Pydantic AI Harness is an official capability library. Its `Shell` capability already provides foreground `run_command`, background `start_command`/`check_command`/`stop_command`, timeout handling, process-group cleanup, cwd handling, output truncation, and env controls.

This is the strongest adjacent implementation. It does not eliminate the standalone gap because it is one framework implementation, not a reusable cross-client fixture corpus. It should be the first validation adapter and a kill signal if all useful fixtures become Pydantic-specific tests.

Gate impact: standalone gap `PASS`; upstream-insufficiency `PASS` only if a second adapter shape is feasible.

### Agent Client Protocol Terminal Methods

Source: https://github.com/agentclientprotocol/agent-client-protocol

ACP defines terminal methods including command creation, output, wait, kill, and release. It is a natural future integration or upstream destination for protocol-level cases. It does not currently appear to provide OS-level process semantics fixtures for client implementations.

Gate impact: standalone gap `PASS`; route fixtures upstream later if ACP maintainers want them.

### gob

Source: https://github.com/juanibiapina/gob

`gob` is a process manager for AI agents and humans. It provides background jobs, logs, lifecycle control, port monitoring, reliable child-process shutdown, persistence, and stuck detection. It solves the user workflow of managing long-running jobs, not validating whether an existing agent shell runner honors a contract.

Gate impact: does not cover the conformance-suite gap.

### cc-reaper

Source: https://github.com/theQuert/cc-reaper

`cc-reaper` cleans up orphan Claude Code, MCP, plugin, browser, Puppeteer, and Codex-related processes. It is a cleanup and guard utility for leaked processes, not a fixture-based shell command semantics suite.

Gate impact: does not cover the conformance-suite gap.

## Standalone Gap

The validated standalone gap is narrow:

> a local, reusable, issue-derived shell command contract suite for coding-agent clients and harnesses.

This is not a general process manager, terminal benchmark, prompt package, dashboard, or log summarizer.

## Distribution Path

- Affected public issue threads in Codex, Claude Code, Copilot/VS Code, and Pydantic AI Harness can use fixture reports as reproducible evidence.
- ACP client and SDK implementers are a natural audience if an ACP adapter proves feasible.
- Pydantic AI Harness is a natural first adapter because its shell implementation is public and current.
- Terminal-Bench and AttractorBench communities are adjacent benchmark audiences, but no adoption is claimed.
- GitHub search/package search terms: `coding agent shell timeout`, `agent shell process cleanup`, `AI agent background process`, `agent terminal conformance`, `agent shell contract`, `MCP coding agent shell runner`.

## Success Criteria

- At least six fixtures map directly to public pain signals.
- Fixture run against Pydantic AI Harness produces meaningful pass/fail output.
- At least one second adapter shape is validated before publication: ACP terminal client, Codex/Claude headless shell surface, or a documented harness adapter.
- Reports are actionable enough to attach to an upstream bug report.
- Fixture cleanup leaves no owned child process or port listener alive.

## Kill Or Reposition Criteria

- Kill if the first build becomes only a Pydantic AI Harness test plugin.
- Kill if ACP, AttractorBench, Terminal-Bench, or Pydantic AI Harness already accepts the exact fixture suite before a standalone value exists.
- Kill if stable adapters require brittle UI automation or paid model calls for basic shell semantics.
- Kill if fixtures cannot avoid destructive commands or broad process killing.
- Route upstream if the useful result is a small ACP or Pydantic test contribution rather than an owned project.

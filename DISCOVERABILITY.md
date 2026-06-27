# Discoverability Gate

Status: `PASS` for private incubation readiness. Public publication still depends on repository creation, CI, metadata verification, and public cooldown.

## Problem and Search Terms

README title and first paragraph state the exact problem and target user: coding-agent client authors, agent harness maintainers, and advanced users debugging shell timeout, process cleanup, background process, terminal output, cwd drift, environment boundary, and PTY behavior.

Natural search terms included in README, package metadata, and docs:

- coding-agent shell timeout
- agent shell process cleanup
- AI agent background process
- terminal output lost
- process-tree cleanup
- shell runner conformance
- ACP terminal methods
- Pydantic AI Harness Shell

## Artifacts Reviewed

- `README.md`
- `pyproject.toml`
- `PRODUCT_SPEC.md`
- `DEMAND_EVIDENCE.md`
- `EVALUATION_PLAN.md`
- `VALIDATION_RESULTS.md`
- `BENCHMARK_RESULTS.md`
- `RELEASE_NOTES.md`
- `ADAPTERS.md`
- `SECURITY.md`
- saved reports under `reports/`

## Distribution Plan

Concrete channels and search surfaces after private CI passes:

- GitHub repository description and topics for `coding-agent`, `shell`, `terminal`, `process-cleanup`, `conformance`, `agent-client-protocol`, and `developer-tools`.
- PyPI metadata after package release, if packaging is pursued.
- Issue-derived reports attached to relevant upstream issues only when they reproduce a specific failure.
- ACP implementer discussions only with concrete adapter findings.
- Pydantic AI Harness issue or PR only if maintainers want the `output-after-kill` fixture or behavior change.

No adoption, users, maintainer interest, benchmark superiority, or traction is claimed.

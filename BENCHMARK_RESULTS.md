# Benchmark Results

This benchmark is a reproducible fixture-run summary, not a claim of adoption or superiority.

- Fixture count: 9
- Manual baseline commands replaced: 5
- Benchmark runtime: 5.137s

## Manual Baseline

- `ps -ef`
- `lsof -iTCP -sTCP:LISTEN -n -P`
- `kill <pid>`
- `pkill -P <pid>`
- `python3 repro.py`

## Adapter Results

### subprocess-reference

- `PASS`: 8
- `SKIP`: 1
- Duration: `2.452s`

### codex-app-server

- `PASS`: 8
- `SKIP`: 1
- Duration: `2.470s`

## Gate Impact

- Reproducible fixture benchmark: `PASS` for adapters that run locally.
- Workflow improvement: `PASS` for replacing ad hoc `ps`/`lsof`/kill/repro scripts with one command and machine-readable reports.
- Windows coverage: `PASS` in GitHub Actions run `30435210271`; the reference adapter passed all 9 fixtures on `windows-latest` for Python 3.10, 3.11, and 3.12.

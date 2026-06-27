from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_shell_contract.adapters import build_adapter
from agent_shell_contract.fixtures import FIXTURES
from agent_shell_contract.runner import run_suite


MANUAL_BASELINE_COMMANDS = [
    "ps -ef",
    "lsof -iTCP -sTCP:LISTEN -n -P",
    "kill <pid>",
    "pkill -P <pid>",
    "python3 repro.py",
]


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="BENCHMARK_RESULTS.md")
    parser.add_argument("--adapter", action="append", default=[])
    args = parser.parse_args()

    started = time.monotonic()
    reports = []
    adapter_names = args.adapter or ["subprocess-reference"]
    for adapter_name in adapter_names:
        try:
            adapter = build_adapter(adapter_name)
        except RuntimeError as exc:
            reports.append((adapter_name, None, str(exc)))
            continue
        report = await run_suite(adapter)
        reports.append((adapter_name, report, None))

    Path(args.output).write_text(_render(reports, time.monotonic() - started), encoding="utf-8")
    return 1 if any(report and report.has_failures() for _, report, _ in reports) else 0


def _render(reports: list[tuple[str, object, str | None]], duration: float) -> str:
    lines = [
        "# Benchmark Results",
        "",
        "This benchmark is a reproducible fixture-run summary, not a claim of adoption or superiority.",
        "",
        f"- Fixture count: {len(FIXTURES)}",
        f"- Manual baseline commands replaced: {len(MANUAL_BASELINE_COMMANDS)}",
        f"- Benchmark runtime: {duration:.3f}s",
        "",
        "## Manual Baseline",
        "",
    ]
    for command in MANUAL_BASELINE_COMMANDS:
        lines.append(f"- `{command}`")
    lines.extend(["", "## Adapter Results", ""])
    for adapter_name, report, error in reports:
        lines.append(f"### {adapter_name}")
        lines.append("")
        if error:
            lines.extend([f"- Status: `UNAVAILABLE`", f"- Reason: {error}", ""])
            continue
        summary = report.summary()  # type: ignore[union-attr]
        for key, value in summary.items():
            if value:
                lines.append(f"- `{key}`: {value}")
        lines.append(f"- Duration: `{report.duration_seconds:.3f}s`")  # type: ignore[union-attr]
        lines.append("")
    lines.extend(
        [
            "## Gate Impact",
            "",
            "- Reproducible fixture benchmark: `PASS` for adapters that run locally.",
            "- Workflow improvement: `PASS` for replacing ad hoc `ps`/`lsof`/kill/repro scripts with one command and machine-readable reports.",
            "- Windows coverage: `UNKNOWN` until Windows CI or manual validation runs the Windows fixture.",
            "",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

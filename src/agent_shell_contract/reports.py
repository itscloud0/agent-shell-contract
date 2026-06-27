from __future__ import annotations

import json
from typing import Any, Mapping

from .models import RunReport


def render_json(report: RunReport) -> str:
    return json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n"


def render_terminal(report: RunReport) -> str:
    data = report.to_dict()
    counts = data["summary"]
    lines = [
        f"agent-shell-contract adapter={data['adapter']} duration={data['duration_seconds']}s",
        "summary " + " ".join(f"{key}={value}" for key, value in counts.items() if value),
        "",
    ]
    for result in data["results"]:
        lines.append(f"{result['status']:11} {result['fixture']}: {result['summary']}")
    return "\n".join(lines) + "\n"


def render_markdown(report: RunReport) -> str:
    return render_markdown_data(report.to_dict())


def render_markdown_data(data: Mapping[str, Any]) -> str:
    lines = [
        "# agent-shell-contract report",
        "",
        f"- Adapter: `{data['adapter']}`",
        f"- Started: `{data['started_at']}`",
        f"- Platform: `{data['platform']}`",
        f"- Python: `{data['python_version']}`",
        f"- Duration: `{data['duration_seconds']}s`",
        "",
        "## Summary",
        "",
    ]
    for key, value in data["summary"].items():
        if value:
            lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Fixture Results", ""])
    for result in data["results"]:
        lines.extend(
            [
                f"### {result['fixture']} - {result['status']}",
                "",
                result["summary"],
                "",
            ]
        )
        if result["details"]:
            lines.append("Details:")
            for detail in result["details"]:
                lines.append(f"- {detail}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


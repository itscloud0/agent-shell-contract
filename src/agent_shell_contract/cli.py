from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
import sys

from .adapters import available_adapters, build_adapter
from .fixtures import FIXTURES
from .reports import render_json, render_markdown, render_markdown_data, render_terminal
from .runner import run_suite


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.command == "fixtures":
        for fixture in FIXTURES:
            print(f"{fixture.name}\t{fixture.summary}")
        return 0
    if args.command == "run":
        return asyncio.run(_run(args))
    if args.command == "report":
        data = json.loads(Path(args.input).read_text(encoding="utf-8"))
        if args.format == "markdown":
            sys.stdout.write(render_markdown_data(data))
        else:
            sys.stdout.write(json.dumps(data, indent=2, sort_keys=True) + "\n")
        return 0
    parser.print_help()
    return 2


async def _run(args: argparse.Namespace) -> int:
    try:
        adapter = build_adapter(args.adapter)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    report = await run_suite(adapter, list(args.fixture) if args.fixture else None)
    if args.json:
        Path(args.json).write_text(render_json(report), encoding="utf-8")
    if args.markdown:
        Path(args.markdown).write_text(render_markdown(report), encoding="utf-8")
    if args.format == "json":
        sys.stdout.write(render_json(report))
    elif args.format == "markdown":
        sys.stdout.write(render_markdown(report))
    else:
        sys.stdout.write(render_terminal(report))
    return 1 if report.has_failures() else 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent-shell-contract")
    subparsers = parser.add_subparsers(dest="command")

    run = subparsers.add_parser("run", help="run shell semantics fixtures")
    run.add_argument("--adapter", choices=available_adapters(), default="subprocess-reference")
    run.add_argument("--fixture", action="append", default=[], help="fixture name; may be repeated")
    run.add_argument("--format", choices=["terminal", "json", "markdown"], default="terminal")
    run.add_argument("--json", help="write JSON report to this path")
    run.add_argument("--markdown", help="write Markdown report to this path")

    subparsers.add_parser("fixtures", help="list available fixtures")

    report = subparsers.add_parser("report", help="render a saved JSON report")
    report.add_argument("--input", required=True)
    report.add_argument("--format", choices=["json", "markdown"], default="markdown")
    return parser


if __name__ == "__main__":
    raise SystemExit(main())

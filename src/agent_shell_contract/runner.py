from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import platform
import sys
import tempfile
import time
from pathlib import Path

from .adapters import ShellAdapter
from .fixtures import select_fixtures
from .models import FixtureResult, FixtureStatus, RunReport


async def run_suite(adapter: ShellAdapter, fixture_names: list[str] | None = None) -> RunReport:
    started = datetime.now(timezone.utc)
    start = time.monotonic()
    results: list[FixtureResult] = []
    try:
        for fixture in select_fixtures(fixture_names):
            with tempfile.TemporaryDirectory(prefix=f"asc-{fixture.name}-") as tmp:
                workdir = Path(tmp)
                fixture_start = time.monotonic()
                try:
                    result = await asyncio.wait_for(fixture.run(adapter, workdir), timeout=fixture.max_seconds)
                except asyncio.TimeoutError:
                    result = FixtureResult(
                        fixture=fixture.name,
                        adapter=adapter.name,
                        status=FixtureStatus.ERROR,
                        summary=f"fixture exceeded {fixture.max_seconds}s",
                        duration_seconds=time.monotonic() - fixture_start,
                    )
                except Exception as exc:  # pragma: no cover - defensive report path
                    result = FixtureResult(
                        fixture=fixture.name,
                        adapter=adapter.name,
                        status=FixtureStatus.ERROR,
                        summary=f"{type(exc).__name__}: {exc}",
                        duration_seconds=time.monotonic() - fixture_start,
                    )
                results.append(result)
    finally:
        await adapter.cleanup()
    return RunReport(
        adapter=adapter.name,
        capabilities=adapter.capabilities,
        started_at=started.strftime("%Y-%m-%dT%H:%M:%SZ"),
        duration_seconds=time.monotonic() - start,
        results=results,
        python_version=sys.version.split()[0],
        platform=platform.platform(),
    )


from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import platform
from typing import Any


class FixtureStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"
    UNSUPPORTED = "UNSUPPORTED"
    ERROR = "ERROR"


@dataclass(frozen=True)
class AdapterCapabilities:
    name: str
    allocates_pty: bool | None = False
    supports_background: bool = True
    supports_env_override: bool = True
    supports_sticky_cwd: bool = False
    platform: str = field(default_factory=lambda: platform.system().lower())

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "allocates_pty": self.allocates_pty,
            "supports_background": self.supports_background,
            "supports_env_override": self.supports_env_override,
            "supports_sticky_cwd": self.supports_sticky_cwd,
            "platform": self.platform,
        }


@dataclass(frozen=True)
class CommandResult:
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    timed_out: bool = False
    duration_seconds: float = 0.0
    raw: str = ""
    unsupported_reason: str | None = None

    def combined_output(self) -> str:
        return "\n".join(part for part in (self.stdout, self.stderr, self.raw) if part)

    def to_dict(self) -> dict[str, Any]:
        return {
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "timed_out": self.timed_out,
            "duration_seconds": round(self.duration_seconds, 4),
            "raw": self.raw,
            "unsupported_reason": self.unsupported_reason,
        }


@dataclass(frozen=True)
class BackgroundHandle:
    id: str
    pid: int | None = None
    command: str = ""
    raw: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "pid": self.pid, "command": self.command, "raw": self.raw}


@dataclass(frozen=True)
class BackgroundStatus:
    running: bool
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    raw: str = ""

    def combined_output(self) -> str:
        return "\n".join(part for part in (self.stdout, self.stderr, self.raw) if part)

    def to_dict(self) -> dict[str, Any]:
        return {
            "running": self.running,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "raw": self.raw,
        }


@dataclass(frozen=True)
class FixtureResult:
    fixture: str
    adapter: str
    status: FixtureStatus
    summary: str
    duration_seconds: float
    details: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "fixture": self.fixture,
            "adapter": self.adapter,
            "status": self.status.value,
            "summary": self.summary,
            "duration_seconds": round(self.duration_seconds, 4),
            "details": list(self.details),
            "evidence": _jsonable(self.evidence),
        }


@dataclass(frozen=True)
class RunReport:
    adapter: str
    capabilities: AdapterCapabilities
    started_at: str
    duration_seconds: float
    results: list[FixtureResult]
    python_version: str
    platform: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "adapter": self.adapter,
            "capabilities": self.capabilities.to_dict(),
            "started_at": self.started_at,
            "duration_seconds": round(self.duration_seconds, 4),
            "python_version": self.python_version,
            "platform": self.platform,
            "summary": self.summary(),
            "results": [result.to_dict() for result in self.results],
        }

    def summary(self) -> dict[str, int]:
        counts = {status.value: 0 for status in FixtureStatus}
        for result in self.results:
            counts[result.status.value] += 1
        return counts

    def has_failures(self) -> bool:
        return any(result.status in {FixtureStatus.FAIL, FixtureStatus.ERROR} for result in self.results)


def _jsonable(value: Any) -> Any:
    if isinstance(value, CommandResult):
        return value.to_dict()
    if isinstance(value, BackgroundHandle):
        return value.to_dict()
    if isinstance(value, BackgroundStatus):
        return value.to_dict()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


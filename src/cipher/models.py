"""Data models for CIPHER's agent and project management.

These are intentionally small, serializable dataclasses so the whole state can
be persisted to (and restored from) a single JSON file.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

# Allowed lifecycle states. Keeping these explicit makes status updates
# validatable and keeps the dashboard output predictable.
AGENT_STATUSES = ("idle", "running", "blocked", "error", "done")
PROJECT_STATUSES = ("planning", "active", "paused", "blocked", "done")


def _now() -> str:
    """UTC timestamp, second precision, ISO-8601."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class Agent:
    """An AI agent that CIPHER coordinates."""

    name: str
    role: str = ""
    status: str = "idle"
    note: str = ""
    updated: str = field(default_factory=_now)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Agent:
        return cls(**data)


@dataclass
class Project:
    """A project CIPHER is tracking, optionally worked on by agents."""

    name: str
    description: str = ""
    status: str = "planning"
    progress: int = 0
    agents: list[str] = field(default_factory=list)
    updated: str = field(default_factory=_now)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Project:
        return cls(**data)

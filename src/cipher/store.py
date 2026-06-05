"""Tiny JSON-file persistence layer for CIPHER state."""

from __future__ import annotations

import json
import os
from pathlib import Path


def default_state_path() -> Path:
    """Where CIPHER stores its state by default.

    Overridable with the ``CIPHER_STATE`` environment variable, which makes
    testing and per-machine configuration straightforward.
    """
    override = os.environ.get("CIPHER_STATE")
    if override:
        return Path(override)
    return Path.home() / ".cipher" / "state.json"


class Store:
    """Loads and saves a JSON document at ``path``."""

    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path is not None else default_state_path()

    def load(self) -> dict:
        if not self.path.exists():
            return {"agents": [], "projects": []}
        with self.path.open(encoding="utf-8") as fh:
            return json.load(fh)

    def save(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, sort_keys=True)

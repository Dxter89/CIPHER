"""CIPHER's persona — its name, role, and how it should respond.

This is the "configure the role and how it should respond" layer. The persona
is composed into a system prompt that CIPHER sends to the robot's onboard LLM
(e.g. DeepSeek), so the same hardware can behave like a calm Jarvis or anything
else you describe — no model training required.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, fields
from pathlib import Path


def default_persona_path() -> Path:
    """Where the persona is stored (override with ``CIPHER_PERSONA``)."""
    override = os.environ.get("CIPHER_PERSONA")
    if override:
        return Path(override)
    return Path.home() / ".cipher" / "persona.json"


@dataclass
class Persona:
    name: str = "CIPHER"
    role: str = "a calm, precise personal assistant in the spirit of Jarvis"
    style: str = "concise, helpful, and lightly witty"
    address: str = ""  # how it addresses you, e.g. "sir" — empty = neutral
    language: str = "English"
    voice_rate: int = 175  # speaking speed hint for TTS backends
    wake_word: str = "cipher"

    # -- editing ----------------------------------------------------------
    @classmethod
    def field_names(cls) -> list[str]:
        return [f.name for f in fields(cls)]

    def set(self, field: str, value: str) -> None:
        """Update one field, coercing types as needed."""
        if field not in self.field_names():
            raise ValueError(
                f"Unknown persona field '{field}'. "
                f"Options: {', '.join(self.field_names())}."
            )
        if field == "voice_rate":
            try:
                setattr(self, field, int(value))
            except ValueError as exc:
                raise ValueError("voice_rate must be a whole number.") from exc
        else:
            setattr(self, field, value)

    # -- the important bit ------------------------------------------------
    def system_prompt(self) -> str:
        """Compose the instruction sent to the robot's LLM."""
        parts = [
            f"You are {self.name}, {self.role}.",
            f"Speak in a manner that is {self.style}.",
        ]
        if self.address:
            parts.append(f"Address the user as '{self.address}'.")
        parts.append(f"Respond in {self.language}.")
        parts.append(
            "Replies are spoken aloud, so keep them short and natural to hear."
        )
        return " ".join(parts)

    # -- persistence ------------------------------------------------------
    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Persona:
        known = {k: v for k, v in data.items() if k in cls.field_names()}
        return cls(**known)

    def save(self, path: Path | str | None = None) -> None:
        target = Path(path) if path is not None else default_persona_path()
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2, sort_keys=True)

    @classmethod
    def load(cls, path: Path | str | None = None) -> Persona:
        target = Path(path) if path is not None else default_persona_path()
        if not target.exists():
            return cls()
        with target.open(encoding="utf-8") as fh:
            return cls.from_dict(json.load(fh))

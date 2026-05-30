"""Core assistant logic for CIPHER.

The :class:`Assistant` routes a line of user input to a registered skill and
returns a text response. Skills are small callables, which keeps the core easy
to extend as CIPHER grows toward a fuller Jarvis-style helper.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

# A skill takes the remaining argument string and returns a response.
Skill = Callable[[str], str]


class Assistant:
    """A minimal, extensible command-routing assistant."""

    def __init__(self, name: str = "CIPHER") -> None:
        self.name = name
        self._skills: dict[str, Skill] = {}
        self._register_builtins()

    def register(self, command: str, skill: Skill) -> None:
        """Register a skill under a command keyword."""
        self._skills[command.lower()] = skill

    @property
    def commands(self) -> list[str]:
        return sorted(self._skills)

    def respond(self, text: str) -> str:
        """Route a line of input to a skill and return its response."""
        text = text.strip()
        if not text:
            return "I'm listening. Type 'help' to see what I can do."

        command, _, argument = text.partition(" ")
        skill = self._skills.get(command.lower())
        if skill is None:
            return (
                f"I don't know how to '{command}' yet. "
                "Type 'help' to see available commands."
            )
        return skill(argument.strip())

    def _register_builtins(self) -> None:
        self.register("help", self._help)
        self.register("hello", lambda _: f"Hello. {self.name} at your service.")
        self.register("time", lambda _: f"The time is {datetime.now():%H:%M:%S}.")
        self.register("date", lambda _: f"Today is {datetime.now():%A, %d %B %Y}.")
        self.register("echo", lambda arg: arg or "(nothing to echo)")

    def _help(self, _: str) -> str:
        listing = ", ".join(self.commands)
        return f"I can help with: {listing}."

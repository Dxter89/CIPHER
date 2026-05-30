"""Core assistant logic for CIPHER.

The :class:`Assistant` routes a line of user input to a registered skill and
returns a text response. Skills are small callables, which keeps the core easy
to extend as CIPHER grows toward a fuller Jarvis-style helper.

On top of the built-in conversational skills, CIPHER coordinates your AI agents
and projects through a persistent :class:`~cipher.manager.Manager`.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from cipher.manager import Manager, ManagerError

# A skill takes the remaining argument string and returns a response.
Skill = Callable[[str], str]


class Assistant:
    """A minimal, extensible command-routing assistant."""

    def __init__(self, name: str = "CIPHER", manager: Manager | None = None) -> None:
        self.name = name
        self.manager = manager if manager is not None else Manager()
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
        try:
            return skill(argument.strip())
        except ManagerError as exc:
            return f"Sorry — {exc}"

    # -- built-in skills --------------------------------------------------
    def _register_builtins(self) -> None:
        self.register("help", self._help)
        self.register("hello", lambda _: f"Hello. {self.name} at your service.")
        self.register("time", lambda _: f"The time is {datetime.now():%H:%M:%S}.")
        self.register("date", lambda _: f"Today is {datetime.now():%A, %d %B %Y}.")
        self.register("echo", lambda arg: arg or "(nothing to echo)")
        # Coordination skills.
        self.register("status", lambda _: self.manager.summary())
        self.register("agent", self._agent)
        self.register("project", self._project)
        self.register("assign", self._assign)

    def _help(self, _: str) -> str:
        return (
            "I can help with:\n"
            "  hello | time | date | echo <text>\n"
            "  status                         — full briefing on agents & projects\n"
            "  agent add <name> [role]        — register an AI agent\n"
            "  agent list                     — list agents\n"
            "  agent status <name> <state> [note]\n"
            "  agent rm <name>\n"
            "  project add <name> [description]\n"
            "  project list\n"
            "  project status <name> <state>\n"
            "  project progress <name> <0-100>\n"
            "  project rm <name>\n"
            "  assign <agent> to <project>"
        )

    # -- agent command ----------------------------------------------------
    def _agent(self, arg: str) -> str:
        sub, _, rest = arg.partition(" ")
        sub, rest = sub.lower(), rest.strip()

        if sub in ("list", "ls", ""):
            agents = sorted(self.manager.agents.values(), key=lambda a: a.name)
            if not agents:
                return "No agents registered. Add one with: agent add <name> [role]"
            return "\n".join(
                f"• {a.name}: {a.status}" + (f" ({a.role})" if a.role else "")
                for a in agents
            )
        if sub == "add":
            name, _, role = rest.partition(" ")
            if not name:
                return "Usage: agent add <name> [role]"
            role = role.strip()
            self.manager.add_agent(name, role)
            return f"Registered agent '{name}'." + (f" Role: {role}" if role else "")
        if sub in ("rm", "remove", "delete"):
            if not rest:
                return "Usage: agent rm <name>"
            self.manager.remove_agent(rest)
            return f"Removed agent '{rest}'."
        if sub == "status":
            name, _, tail = rest.partition(" ")
            new_status, _, note = tail.partition(" ")
            if not name or not new_status:
                return "Usage: agent status <name> <state> [note]"
            a = self.manager.set_agent_status(name, new_status.lower(), note.strip())
            return f"{a.name} is now '{a.status}'." + (f" ({a.note})" if a.note else "")
        return f"Unknown agent command '{sub}'. Try: add, list, status, rm."

    # -- project command --------------------------------------------------
    def _project(self, arg: str) -> str:
        sub, _, rest = arg.partition(" ")
        sub, rest = sub.lower(), rest.strip()

        if sub in ("list", "ls", ""):
            projects = sorted(self.manager.projects.values(), key=lambda p: p.name)
            if not projects:
                return "No projects tracked. Add one with: project add <name> [description]"
            return "\n".join(
                f"• {p.name}: {p.status} ({p.progress}%)" for p in projects
            )
        if sub == "add":
            name, _, desc = rest.partition(" ")
            if not name:
                return "Usage: project add <name> [description]"
            self.manager.add_project(name, desc.strip())
            return f"Tracking project '{name}'."
        if sub in ("rm", "remove", "delete"):
            if not rest:
                return "Usage: project rm <name>"
            self.manager.remove_project(rest)
            return f"Stopped tracking project '{rest}'."
        if sub == "status":
            name, _, new_status = rest.partition(" ")
            if not name or not new_status:
                return "Usage: project status <name> <state>"
            p = self.manager.set_project_status(name, new_status.strip().lower())
            return f"Project '{p.name}' is now '{p.status}'."
        if sub == "progress":
            name, _, value = rest.partition(" ")
            if not name or not value.strip():
                return "Usage: project progress <name> <0-100>"
            try:
                pct = int(value.strip())
            except ValueError:
                return "Progress must be a whole number between 0 and 100."
            p = self.manager.set_project_progress(name, pct)
            return f"Project '{p.name}' is at {p.progress}% ({p.status})."
        return f"Unknown project command '{sub}'. Try: add, list, status, progress, rm."

    # -- assign command ---------------------------------------------------
    def _assign(self, arg: str) -> str:
        # Accept "agent to project" or "agent project".
        tokens = [t for t in arg.replace(" to ", " ").split() if t]
        if len(tokens) != 2:
            return "Usage: assign <agent> to <project>"
        agent_name, project_name = tokens
        p = self.manager.assign(agent_name, project_name)
        return f"Assigned '{agent_name}' to project '{p.name}'. Crew: {', '.join(p.agents)}."

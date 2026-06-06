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

from cipher.desktop import DesktopError, open_app, show_desktop
from cipher.manager import Manager, ManagerError
from cipher.persona import Persona
from cipher.robot import HttpRobot, MockRobot, RobotError, connect

# A skill takes the remaining argument string and returns a response.
Skill = Callable[[str], str]


class Assistant:
    """A minimal, extensible command-routing assistant."""

    def __init__(
        self,
        name: str = "CIPHER",
        manager: Manager | None = None,
        persona: Persona | None = None,
        persona_path=None,
        robot: HttpRobot | MockRobot | None = None,
    ) -> None:
        self.name = name
        self.manager = manager if manager is not None else Manager()
        self._persona_path = persona_path
        self.persona = persona if persona is not None else Persona.load(persona_path)
        self.robot = robot if robot is not None else connect()
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
        except (ManagerError, RobotError, DesktopError, ValueError) as exc:
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
        # Voice / robot skills.
        self.register("persona", self._persona)
        self.register("ask", self._ask)
        self.register("say", self._say)
        # Desktop skills.
        self.register("desktop", self._desktop)

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
            "  assign <agent> to <project>\n"
            "  persona                        — show CIPHER's persona\n"
            "  persona set <field> <value>    — change role/style/etc.\n"
            "  ask <message>                  — talk to the robot's LLM\n"
            "  say <text>                     — make the robot speak verbatim\n"
            "  desktop                        — show the desktop (minimise all windows)\n"
            "  desktop launch <app>           — open an application by name"
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

    # -- persona command --------------------------------------------------
    def _persona(self, arg: str) -> str:
        sub, _, rest = arg.partition(" ")
        sub, rest = sub.lower(), rest.strip()

        if sub in ("", "show"):
            p = self.persona
            return (
                f"Persona '{p.name}':\n"
                f"  role:       {p.role}\n"
                f"  style:      {p.style}\n"
                f"  address:    {p.address or '(neutral)'}\n"
                f"  language:   {p.language}\n"
                f"  voice_rate: {p.voice_rate}\n"
                f"  wake_word:  {p.wake_word}\n"
                f"System prompt sent to the robot:\n  {self.persona.system_prompt()}"
            )
        if sub == "set":
            field, _, value = rest.partition(" ")
            if not field or not value.strip():
                return (
                    "Usage: persona set <field> <value>\n"
                    f"Fields: {', '.join(Persona.field_names())}"
                )
            self.persona.set(field.lower(), value.strip())
            self.persona.save(self._persona_path)
            return f"Persona updated: {field.lower()} = {value.strip()}"
        return f"Unknown persona command '{sub}'. Try: show, set."

    # -- ask / say (robot voice) ------------------------------------------
    def _ask(self, arg: str) -> str:
        if not arg:
            return "Usage: ask <message>"
        return self.robot.ask(arg, self.persona.system_prompt())

    def _say(self, arg: str) -> str:
        if not arg:
            return "Usage: say <text>"
        self.robot.say(arg)
        if not getattr(self.robot, "configured", False):
            return "(No robot connected — set CIPHER_ROBOT_URL to make it speak.)"
        return f"Speaking: {arg}"

    # -- desktop skills ---------------------------------------------------
    def _desktop(self, arg: str) -> str:
        sub, _, rest = arg.partition(" ")
        sub = sub.lower()

        if sub in ("", "show", "open"):
            return show_desktop()
        if sub in ("launch", "start", "run"):
            if not rest:
                return "Usage: desktop launch <app>"
            return open_app(rest.strip())
        # Treat any unrecognised sub-command as an app name to open, so that
        # "desktop firefox" works as well as "desktop launch firefox".
        return open_app(arg.strip())

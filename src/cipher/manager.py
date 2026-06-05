"""The coordination layer: register agents, track projects, persist state.

:class:`Manager` is the heart of CIPHER's Jarvis-style coordination. It holds
the in-memory state, validates status transitions, and writes through to a
:class:`~cipher.store.Store` after every mutation so nothing is lost between
runs.
"""

from __future__ import annotations

from cipher.models import (
    AGENT_STATUSES,
    PROJECT_STATUSES,
    Agent,
    Project,
    _now,
)
from cipher.store import Store


class ManagerError(Exception):
    """Raised for invalid operations (unknown name, bad status, duplicate)."""


class Manager:
    def __init__(self, store: Store | None = None) -> None:
        self.store = store or Store()
        data = self.store.load()
        self.agents: dict[str, Agent] = {
            a["name"]: Agent.from_dict(a) for a in data.get("agents", [])
        }
        self.projects: dict[str, Project] = {
            p["name"]: Project.from_dict(p) for p in data.get("projects", [])
        }

    # -- persistence ------------------------------------------------------
    def _save(self) -> None:
        self.store.save(
            {
                "agents": [a.to_dict() for a in self.agents.values()],
                "projects": [p.to_dict() for p in self.projects.values()],
            }
        )

    # -- agents -----------------------------------------------------------
    def add_agent(self, name: str, role: str = "") -> Agent:
        if name in self.agents:
            raise ManagerError(f"Agent '{name}' already exists.")
        agent = Agent(name=name, role=role)
        self.agents[name] = agent
        self._save()
        return agent

    def remove_agent(self, name: str) -> None:
        if name not in self.agents:
            raise ManagerError(f"No agent named '{name}'.")
        del self.agents[name]
        # Detach from any projects that referenced it.
        for project in self.projects.values():
            if name in project.agents:
                project.agents.remove(name)
        self._save()

    def set_agent_status(self, name: str, status: str, note: str = "") -> Agent:
        agent = self.agents.get(name)
        if agent is None:
            raise ManagerError(f"No agent named '{name}'.")
        if status not in AGENT_STATUSES:
            raise ManagerError(
                f"Invalid status '{status}'. Choose from: {', '.join(AGENT_STATUSES)}."
            )
        agent.status = status
        if note:
            agent.note = note
        agent.updated = _now()
        self._save()
        return agent

    # -- projects ---------------------------------------------------------
    def add_project(self, name: str, description: str = "") -> Project:
        if name in self.projects:
            raise ManagerError(f"Project '{name}' already exists.")
        project = Project(name=name, description=description)
        self.projects[name] = project
        self._save()
        return project

    def remove_project(self, name: str) -> None:
        if name not in self.projects:
            raise ManagerError(f"No project named '{name}'.")
        del self.projects[name]
        self._save()

    def set_project_status(self, name: str, status: str) -> Project:
        project = self.projects.get(name)
        if project is None:
            raise ManagerError(f"No project named '{name}'.")
        if status not in PROJECT_STATUSES:
            raise ManagerError(
                f"Invalid status '{status}'. Choose from: {', '.join(PROJECT_STATUSES)}."
            )
        project.status = status
        project.updated = _now()
        self._save()
        return project

    def set_project_progress(self, name: str, progress: int) -> Project:
        project = self.projects.get(name)
        if project is None:
            raise ManagerError(f"No project named '{name}'.")
        if not 0 <= progress <= 100:
            raise ManagerError("Progress must be between 0 and 100.")
        project.progress = progress
        if progress == 100:
            project.status = "done"
        project.updated = _now()
        self._save()
        return project

    def assign(self, agent_name: str, project_name: str) -> Project:
        if agent_name not in self.agents:
            raise ManagerError(f"No agent named '{agent_name}'.")
        project = self.projects.get(project_name)
        if project is None:
            raise ManagerError(f"No project named '{project_name}'.")
        if agent_name not in project.agents:
            project.agents.append(agent_name)
            project.updated = _now()
            self._save()
        return project

    # -- overview ---------------------------------------------------------
    def summary(self) -> str:
        """A Jarvis-style status briefing across agents and projects."""
        lines: list[str] = []
        if self.agents:
            lines.append("Agents:")
            for a in sorted(self.agents.values(), key=lambda x: x.name):
                role = f" ({a.role})" if a.role else ""
                note = f" — {a.note}" if a.note else ""
                lines.append(f"  • {a.name}{role}: {a.status}{note}")
        else:
            lines.append("Agents: none registered.")

        if self.projects:
            lines.append("Projects:")
            for p in sorted(self.projects.values(), key=lambda x: x.name):
                crew = f" [{', '.join(p.agents)}]" if p.agents else ""
                lines.append(f"  • {p.name}: {p.status} ({p.progress}%){crew}")
        else:
            lines.append("Projects: none tracked.")
        return "\n".join(lines)

"""CIPHER — a personal, Jarvis-style assistant."""

__version__ = "0.1.0"

from cipher.assistant import Assistant
from cipher.manager import Manager
from cipher.models import Agent, Project
from cipher.persona import Persona
from cipher.robot import HttpRobot, MockRobot, RobotConfig, connect

__all__ = [
    "Assistant",
    "Manager",
    "Agent",
    "Project",
    "Persona",
    "RobotConfig",
    "HttpRobot",
    "MockRobot",
    "connect",
    "__version__",
]

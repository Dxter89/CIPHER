"""Tests for the assistant's persona / ask / say commands."""

import pytest

from cipher.assistant import Assistant
from cipher.manager import Manager
from cipher.persona import Persona
from cipher.robot import MockRobot
from cipher.store import Store


class RecordingRobot(MockRobot):
    """A configured robot that records calls for assertions."""

    configured = True

    def __init__(self):
        self.asked = []
        self.said = []

    def ask(self, message, system=""):
        self.asked.append((message, system))
        return f"reply to: {message}"

    def say(self, text):
        self.said.append(text)


@pytest.fixture
def assistant(tmp_path):
    return Assistant(
        manager=Manager(Store(tmp_path / "state.json")),
        persona=Persona(),
        persona_path=tmp_path / "persona.json",
        robot=RecordingRobot(),
    )


def test_persona_show_lists_role(assistant):
    out = assistant.respond("persona")
    assert "role:" in out
    assert "Jarvis" in out


def test_persona_set_persists(assistant, tmp_path):
    assistant.respond("persona set address sir")
    assert assistant.persona.address == "sir"
    # A fresh load from the same path sees the change.
    assert Persona.load(tmp_path / "persona.json").address == "sir"


def test_persona_set_unknown_field_is_graceful(assistant):
    assert "Sorry" in assistant.respond("persona set color blue")


def test_ask_routes_message_and_persona_to_robot(assistant):
    out = assistant.respond("ask what's my status")
    assert out == "reply to: what's my status"
    message, system = assistant.robot.asked[0]
    assert message == "what's my status"
    assert "CIPHER" in system  # persona system prompt was attached


def test_say_speaks_through_robot(assistant):
    out = assistant.respond("say good morning")
    assert assistant.robot.said == ["good morning"]
    assert "Speaking" in out


def test_say_without_robot_warns(tmp_path):
    offline = Assistant(
        manager=Manager(Store(tmp_path / "s.json")),
        persona_path=tmp_path / "p.json",
        robot=MockRobot(),
    )
    assert "No robot connected" in offline.respond("say hi")

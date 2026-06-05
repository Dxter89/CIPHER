"""Tests for the assistant's agent/project/status commands."""

import pytest

from cipher.assistant import Assistant
from cipher.manager import Manager
from cipher.store import Store


@pytest.fixture
def assistant(tmp_path):
    return Assistant(manager=Manager(Store(tmp_path / "state.json")))


def test_agent_add_and_list(assistant):
    assert "Registered" in assistant.respond("agent add scout research")
    listing = assistant.respond("agent list")
    assert "scout" in listing


def test_agent_status_update(assistant):
    assistant.respond("agent add scout")
    reply = assistant.respond("agent status scout running crawling docs")
    assert "running" in reply
    assert "crawling docs" in reply


def test_project_lifecycle(assistant):
    assistant.respond("project add cipher jarvis assistant")
    assistant.respond("project progress cipher 100")
    listing = assistant.respond("project list")
    assert "done" in listing
    assert "100%" in listing


def test_assign_and_status_dashboard(assistant):
    assistant.respond("agent add scout")
    assistant.respond("project add cipher")
    assistant.respond("assign scout to cipher")
    dashboard = assistant.respond("status")
    assert "scout" in dashboard
    assert "cipher" in dashboard


def test_error_is_reported_gracefully(assistant):
    reply = assistant.respond("agent status ghost running")
    assert "Sorry" in reply


def test_invalid_status_lists_valid_options(assistant):
    assistant.respond("agent add scout")
    reply = assistant.respond("agent status scout napping")
    assert "Invalid status" in reply

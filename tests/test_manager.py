"""Tests for the agent/project coordination layer."""

import pytest

from cipher.manager import Manager, ManagerError
from cipher.store import Store


@pytest.fixture
def manager(tmp_path):
    """A Manager backed by an isolated temp state file."""
    return Manager(Store(tmp_path / "state.json"))


def test_add_and_list_agent(manager):
    manager.add_agent("scout", role="research")
    assert "scout" in manager.agents
    assert manager.agents["scout"].role == "research"
    assert manager.agents["scout"].status == "idle"


def test_duplicate_agent_rejected(manager):
    manager.add_agent("scout")
    with pytest.raises(ManagerError):
        manager.add_agent("scout")


def test_set_agent_status(manager):
    manager.add_agent("scout")
    manager.set_agent_status("scout", "running", note="crawling docs")
    assert manager.agents["scout"].status == "running"
    assert manager.agents["scout"].note == "crawling docs"


def test_invalid_agent_status_rejected(manager):
    manager.add_agent("scout")
    with pytest.raises(ManagerError):
        manager.set_agent_status("scout", "napping")


def test_project_progress_completes_project(manager):
    manager.add_project("cipher")
    manager.set_project_progress("cipher", 100)
    assert manager.projects["cipher"].status == "done"


def test_progress_out_of_range_rejected(manager):
    manager.add_project("cipher")
    with pytest.raises(ManagerError):
        manager.set_project_progress("cipher", 150)


def test_assign_agent_to_project(manager):
    manager.add_agent("scout")
    manager.add_project("cipher")
    manager.assign("scout", "cipher")
    assert "scout" in manager.projects["cipher"].agents


def test_removing_agent_detaches_from_projects(manager):
    manager.add_agent("scout")
    manager.add_project("cipher")
    manager.assign("scout", "cipher")
    manager.remove_agent("scout")
    assert "scout" not in manager.projects["cipher"].agents


def test_state_persists_across_instances(tmp_path):
    path = tmp_path / "state.json"
    m1 = Manager(Store(path))
    m1.add_agent("scout", role="research")
    m1.add_project("cipher", description="jarvis")
    m1.assign("scout", "cipher")

    # A fresh Manager reading the same file sees everything.
    m2 = Manager(Store(path))
    assert "scout" in m2.agents
    assert "cipher" in m2.projects
    assert "scout" in m2.projects["cipher"].agents


def test_summary_mentions_agents_and_projects(manager):
    manager.add_agent("scout")
    manager.add_project("cipher")
    summary = manager.summary()
    assert "scout" in summary and "cipher" in summary

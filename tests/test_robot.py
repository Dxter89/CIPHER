"""Tests for the robot connector (HTTP + offline mock)."""

import json

import pytest

from cipher.robot import HttpRobot, MockRobot, RobotConfig, RobotError, connect


def test_connect_returns_mock_when_no_url():
    assert isinstance(connect(RobotConfig()), MockRobot)


def test_connect_returns_http_when_url_set():
    assert isinstance(connect(RobotConfig(base_url="http://robot.local")), HttpRobot)


def test_mock_robot_is_offline_and_echoes():
    robot = MockRobot()
    assert robot.configured is False
    assert "offline" in robot.ask("hello").lower()


def test_config_from_env(monkeypatch):
    monkeypatch.setenv("CIPHER_ROBOT_URL", "http://100.64.0.5:8080")
    monkeypatch.setenv("CIPHER_ROBOT_TOKEN", "secret")
    monkeypatch.setenv("CIPHER_ROBOT_REPLY_FIELD", "answer")
    cfg = RobotConfig.from_env()
    assert cfg.base_url == "http://100.64.0.5:8080"
    assert cfg.auth_token == "secret"
    assert cfg.reply_field == "answer"


def _fake_urlopen(captured, response_body):
    """Build a urlopen replacement that records the request and returns a body."""

    class _Resp:
        def read(self):
            return response_body.encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def fake(request, timeout=None):
        captured["url"] = request.full_url
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["headers"] = request.headers
        return _Resp()

    return fake


def test_http_ask_sends_message_and_system(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        "urllib.request.urlopen",
        _fake_urlopen(captured, json.dumps({"reply": "At your service."})),
    )
    robot = HttpRobot(RobotConfig(base_url="http://robot.local", auth_token="tok"))
    reply = robot.ask("status report", system="You are CIPHER.")

    assert reply == "At your service."
    assert captured["url"] == "http://robot.local/api/chat"
    assert captured["body"]["message"] == "status report"
    assert captured["body"]["system"] == "You are CIPHER."
    # Authorization header is attached when a token is configured.
    assert captured["headers"].get("Authorization") == "Bearer tok"


def test_http_ask_raises_when_reply_field_missing(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        "urllib.request.urlopen",
        _fake_urlopen(captured, json.dumps({"unexpected": "shape"})),
    )
    robot = HttpRobot(RobotConfig(base_url="http://robot.local"))
    with pytest.raises(RobotError):
        robot.ask("hi")


def test_http_ask_wraps_bare_string_reply(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        "urllib.request.urlopen",
        _fake_urlopen(captured, "just text, not json"),
    )
    robot = HttpRobot(RobotConfig(base_url="http://robot.local"))
    assert robot.ask("hi") == "just text, not json"


def test_http_unreachable_raises_robot_error(monkeypatch):
    def boom(request, timeout=None):
        raise OSError("connection refused")

    monkeypatch.setattr("urllib.request.urlopen", boom)
    robot = HttpRobot(RobotConfig(base_url="http://robot.local"))
    with pytest.raises(RobotError):
        robot.ask("hi")

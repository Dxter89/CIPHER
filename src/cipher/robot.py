"""Connector to a talking robot device with an onboard LLM (e.g. DeepSeek).

The robot exposes a local HTTP API over your network (Wi-Fi/Tailscale). CIPHER
runs on your laptop, sends it a persona + your message, and the robot replies
(and speaks) using its own model.

The connector is deliberately *config-driven* — endpoint paths and JSON field
names are all configurable — so it can target different devices without code
changes. When no robot address is configured, CIPHER falls back to an offline
:class:`MockRobot` so the rest of the app keeps working.

Only the Python standard library is used (``urllib``), keeping CIPHER
dependency-free and easy to run on a laptop or a Raspberry Pi.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass


class RobotError(Exception):
    """Raised when the robot can't be reached or returns an unexpected reply."""


@dataclass
class RobotConfig:
    """How to talk to the robot's HTTP API.

    Field names are configurable because every device names its JSON keys
    differently. Defaults match a common ``{"message": ...}`` / ``{"reply": ...}``
    chat shape; adjust via environment variables to fit your device.
    """

    base_url: str = ""  # e.g. "http://100.64.0.5:8080" (Tailscale IP works great)
    chat_path: str = "/api/chat"
    say_path: str = "/api/say"  # optional: speak text verbatim
    auth_token: str = ""
    message_field: str = "message"
    system_field: str = "system"
    reply_field: str = "reply"
    text_field: str = "text"
    timeout: float = 30.0

    @classmethod
    def from_env(cls) -> RobotConfig:
        """Build config from CIPHER_ROBOT_* environment variables."""
        env = os.environ
        cfg = cls(
            base_url=env.get("CIPHER_ROBOT_URL", ""),
            auth_token=env.get("CIPHER_ROBOT_TOKEN", ""),
        )
        for attr, var in (
            ("chat_path", "CIPHER_ROBOT_CHAT_PATH"),
            ("say_path", "CIPHER_ROBOT_SAY_PATH"),
            ("message_field", "CIPHER_ROBOT_MESSAGE_FIELD"),
            ("system_field", "CIPHER_ROBOT_SYSTEM_FIELD"),
            ("reply_field", "CIPHER_ROBOT_REPLY_FIELD"),
            ("text_field", "CIPHER_ROBOT_TEXT_FIELD"),
        ):
            if var in env:
                setattr(cfg, attr, env[var])
        if "CIPHER_ROBOT_TIMEOUT" in env:
            cfg.timeout = float(env["CIPHER_ROBOT_TIMEOUT"])
        return cfg


class MockRobot:
    """Offline stand-in used when no robot is configured or for testing."""

    configured = False

    def ask(self, message: str, system: str = "") -> str:
        return (
            "[CIPHER offline — no robot connected] "
            f"I heard: '{message}'. Set CIPHER_ROBOT_URL to connect your device."
        )

    def say(self, text: str) -> None:
        # Nothing to speak through; surface it so the user still sees output.
        print(f"[CIPHER would say]: {text}")


class HttpRobot:
    """Talks to a robot's HTTP API using only the standard library."""

    configured = True

    def __init__(self, config: RobotConfig) -> None:
        self.config = config

    def _post(self, path: str, payload: dict) -> dict:
        url = self.config.base_url.rstrip("/") + path
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(url, data=body, method="POST")
        request.add_header("Content-Type", "application/json")
        if self.config.auth_token:
            request.add_header("Authorization", f"Bearer {self.config.auth_token}")
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout) as resp:
                raw = resp.read().decode("utf-8")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise RobotError(f"Could not reach robot at {url}: {exc}") from exc
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # Some devices return a bare string; wrap it for the caller.
            return {self.config.reply_field: raw}

    def ask(self, message: str, system: str = "") -> str:
        payload: dict = {self.config.message_field: message}
        if system and self.config.system_field:
            payload[self.config.system_field] = system
        data = self._post(self.config.chat_path, payload)
        reply = data.get(self.config.reply_field)
        if reply is None:
            raise RobotError(
                f"Robot reply missing '{self.config.reply_field}' field. "
                f"Got keys: {sorted(data)}."
            )
        return str(reply)

    def say(self, text: str) -> None:
        self._post(self.config.say_path, {self.config.text_field: text})


def connect(config: RobotConfig | None = None) -> MockRobot | HttpRobot:
    """Return an HttpRobot if a base URL is configured, else an offline MockRobot."""
    config = config or RobotConfig.from_env()
    if config.base_url:
        return HttpRobot(config)
    return MockRobot()

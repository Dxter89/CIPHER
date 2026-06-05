"""Tests for the CIPHER assistant core."""

from cipher.assistant import Assistant


def test_hello_responds_with_name():
    assistant = Assistant(name="CIPHER")
    assert "CIPHER" in assistant.respond("hello")


def test_echo_returns_argument():
    assistant = Assistant()
    assert assistant.respond("echo hello world") == "hello world"


def test_empty_input_is_handled():
    assistant = Assistant()
    assert "listening" in assistant.respond("   ").lower()


def test_unknown_command_is_graceful():
    assistant = Assistant()
    reply = assistant.respond("fly")
    assert "don't know" in reply.lower()


def test_help_lists_registered_commands():
    assistant = Assistant()
    reply = assistant.respond("help")
    assert "echo" in reply and "time" in reply


def test_custom_skill_can_be_registered():
    assistant = Assistant()
    assistant.register("ping", lambda _: "pong")
    assert assistant.respond("ping") == "pong"

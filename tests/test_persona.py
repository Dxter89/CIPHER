"""Tests for the persona (role / response configuration) layer."""

import pytest

from cipher.persona import Persona


def test_default_persona_mentions_jarvis_spirit():
    p = Persona()
    assert p.name == "CIPHER"
    assert "Jarvis" in p.role


def test_system_prompt_includes_name_role_and_style():
    p = Persona(name="CIPHER", role="a helpful aide", style="brisk")
    prompt = p.system_prompt()
    assert "CIPHER" in prompt
    assert "helpful aide" in prompt
    assert "brisk" in prompt


def test_address_appears_only_when_set():
    assert "sir" not in Persona().system_prompt()
    assert "sir" in Persona(address="sir").system_prompt()


def test_set_coerces_voice_rate_to_int():
    p = Persona()
    p.set("voice_rate", "200")
    assert p.voice_rate == 200


def test_set_rejects_unknown_field():
    with pytest.raises(ValueError):
        Persona().set("color", "red")


def test_set_rejects_non_numeric_voice_rate():
    with pytest.raises(ValueError):
        Persona().set("voice_rate", "fast")


def test_persona_round_trips_through_disk(tmp_path):
    path = tmp_path / "persona.json"
    p = Persona(name="CIPHER", address="sir")
    p.set("style", "formal and dry")
    p.save(path)

    loaded = Persona.load(path)
    assert loaded.address == "sir"
    assert loaded.style == "formal and dry"


def test_load_missing_file_returns_default(tmp_path):
    loaded = Persona.load(tmp_path / "nope.json")
    assert loaded.name == "CIPHER"

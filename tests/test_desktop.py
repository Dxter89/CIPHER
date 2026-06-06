"""Tests for the desktop skill."""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from cipher.desktop import DesktopError, open_app, show_desktop


# ---------------------------------------------------------------------------
# show_desktop
# ---------------------------------------------------------------------------

class TestShowDesktop:
    def test_linux_wmctrl_success(self):
        with patch("cipher.desktop._system", return_value="Linux"), \
             patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = show_desktop()
        assert result == "Desktop is now showing."
        mock_run.assert_called_once_with(["wmctrl", "-k", "on"], capture_output=True)

    def test_linux_fallback_xdotool(self):
        """When wmctrl fails (non-zero exit), xdotool is tried."""
        with patch("cipher.desktop._system", return_value="Linux"), \
             patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=1),           # wmctrl fails
                MagicMock(returncode=0),           # xdotool succeeds
            ]
            result = show_desktop()
        assert result == "Desktop is now showing."
        assert mock_run.call_count == 2

    def test_linux_tool_missing(self):
        """FileNotFoundError is wrapped into DesktopError."""
        with patch("cipher.desktop._system", return_value="Linux"), \
             patch("subprocess.run", side_effect=FileNotFoundError("wmctrl")):
            with pytest.raises(DesktopError, match="wmctrl"):
                show_desktop()

    def test_darwin_success(self):
        with patch("cipher.desktop._system", return_value="Darwin"), \
             patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = show_desktop()
        assert result == "Desktop is now showing."
        args = mock_run.call_args[0][0]
        assert args[0] == "osascript"

    def test_windows_success(self):
        with patch("cipher.desktop._system", return_value="Windows"), \
             patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = show_desktop()
        assert result == "Desktop is now showing."
        args = mock_run.call_args[0][0]
        assert "powershell" in args[0]

    def test_unsupported_platform(self):
        with patch("cipher.desktop._system", return_value="FreeBSD"):
            with pytest.raises(DesktopError, match="Unsupported"):
                show_desktop()

    def test_subprocess_error(self):
        with patch("cipher.desktop._system", return_value="Darwin"), \
             patch("subprocess.run",
                   side_effect=subprocess.CalledProcessError(1, "osascript")):
            with pytest.raises(DesktopError, match="Command failed"):
                show_desktop()


# ---------------------------------------------------------------------------
# open_app
# ---------------------------------------------------------------------------

class TestOpenApp:
    def test_empty_name_raises(self):
        with pytest.raises(DesktopError, match="No application name"):
            open_app("")

    def test_darwin_success(self):
        with patch("cipher.desktop._system", return_value="Darwin"), \
             patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = open_app("Safari")
        assert result == "Opening 'Safari'."
        args = mock_run.call_args[0][0]
        assert args == ["open", "-a", "Safari"]

    def test_linux_success(self):
        with patch("cipher.desktop._system", return_value="Linux"), \
             patch("subprocess.Popen") as mock_popen:
            result = open_app("firefox")
        assert result == "Opening 'firefox'."
        mock_popen.assert_called_once()

    def test_linux_app_not_found(self):
        with patch("cipher.desktop._system", return_value="Linux"), \
             patch("subprocess.Popen", side_effect=FileNotFoundError):
            with pytest.raises(DesktopError, match="not found"):
                open_app("nonexistent-app")

    def test_windows_success(self):
        with patch("cipher.desktop._system", return_value="Windows"), \
             patch("subprocess.Popen") as mock_popen:
            result = open_app("notepad")
        assert result == "Opening 'notepad'."
        mock_popen.assert_called_once()

    def test_unsupported_platform(self):
        with patch("cipher.desktop._system", return_value="FreeBSD"):
            with pytest.raises(DesktopError, match="Unsupported"):
                open_app("xterm")


# ---------------------------------------------------------------------------
# Assistant integration
# ---------------------------------------------------------------------------

class TestAssistantDesktopCommand:
    def setup_method(self):
        from cipher.assistant import Assistant
        self.assistant = Assistant()

    def test_desktop_show(self):
        with patch("cipher.desktop._system", return_value="Linux"), \
             patch("subprocess.run", return_value=MagicMock(returncode=0)):
            response = self.assistant.respond("desktop")
        assert "Desktop is now showing" in response

    def test_desktop_show_explicit(self):
        with patch("cipher.desktop._system", return_value="Linux"), \
             patch("subprocess.run", return_value=MagicMock(returncode=0)):
            response = self.assistant.respond("desktop show")
        assert "Desktop is now showing" in response

    def test_desktop_open_keyword(self):
        with patch("cipher.desktop._system", return_value="Linux"), \
             patch("subprocess.run", return_value=MagicMock(returncode=0)):
            response = self.assistant.respond("desktop open")
        assert "Desktop is now showing" in response

    def test_desktop_launch_app(self):
        with patch("cipher.desktop._system", return_value="Linux"), \
             patch("subprocess.Popen"):
            response = self.assistant.respond("desktop launch firefox")
        assert "Opening 'firefox'" in response

    def test_desktop_bare_app_name(self):
        """'desktop firefox' is shorthand for 'desktop launch firefox'."""
        with patch("cipher.desktop._system", return_value="Linux"), \
             patch("subprocess.Popen"):
            response = self.assistant.respond("desktop firefox")
        assert "Opening 'firefox'" in response

    def test_desktop_error_surfaced(self):
        with patch("cipher.desktop._system", return_value="Linux"), \
             patch("subprocess.run", side_effect=FileNotFoundError("wmctrl")):
            response = self.assistant.respond("desktop")
        assert "Sorry" in response

    def test_desktop_in_help(self):
        response = self.assistant.respond("help")
        assert "desktop" in response

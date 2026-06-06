"""Desktop interaction skill for CIPHER.

Provides show-desktop (minimise all windows) and application-launch,
using platform-native mechanisms with no third-party dependencies.
"""

from __future__ import annotations

import platform
import subprocess


class DesktopError(Exception):
    """Raised when a desktop operation cannot be completed."""


def _system() -> str:
    return platform.system()


def show_desktop() -> str:
    """Minimise all windows to reveal the desktop."""
    sys = _system()
    try:
        if sys == "Darwin":
            subprocess.run(
                ["osascript", "-e",
                 'tell application "System Events" to keystroke "h" '
                 'using {command down, option down}'],
                check=True, capture_output=True,
            )
        elif sys == "Linux":
            # wmctrl is the most common tool; fall back to xdotool Super+D.
            result = subprocess.run(
                ["wmctrl", "-k", "on"], capture_output=True
            )
            if result.returncode != 0:
                subprocess.run(
                    ["xdotool", "key", "super+d"],
                    check=True, capture_output=True,
                )
        elif sys == "Windows":
            subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "(New-Object -ComObject Shell.Application).MinimizeAll()"],
                check=True, capture_output=True,
            )
        else:
            raise DesktopError(f"Unsupported platform: {sys}")
    except FileNotFoundError as exc:
        raise DesktopError(
            f"Required tool not found ({exc.filename}). "
            "On Linux install wmctrl or xdotool."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise DesktopError(f"Command failed: {exc}") from exc
    return "Desktop is now showing."


def open_app(name: str) -> str:
    """Launch an application by name."""
    if not name:
        raise DesktopError("No application name given.")
    sys = _system()
    try:
        if sys == "Darwin":
            subprocess.run(["open", "-a", name], check=True, capture_output=True)
        elif sys == "Linux":
            # xdg-open handles file associations; for app names use the binary
            # directly and let the shell PATH do the work.
            subprocess.Popen(  # noqa: S603 – intentional app launch
                [name], start_new_session=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        elif sys == "Windows":
            subprocess.Popen(  # noqa: S603
                name, shell=True,  # noqa: S602 – needed for Start-menu names
                start_new_session=True,
            )
        else:
            raise DesktopError(f"Unsupported platform: {sys}")
    except FileNotFoundError:
        raise DesktopError(
            f"Application '{name}' not found. "
            "Check the name and make sure it is on your PATH."
        )
    except subprocess.CalledProcessError as exc:
        raise DesktopError(f"Could not launch '{name}': {exc}") from exc
    return f"Opening '{name}'."

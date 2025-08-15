"""
Cross-platform clipboard access helper module.

Provides abstracted clipboard functionality that works across different platforms
including native Linux/macOS/Windows and WSL environments.
"""

import os
import platform
import subprocess
import sys
from typing import Optional


class ClipboardError(Exception):
    """Raised when clipboard operations fail."""

    pass


def get_clipboard_content() -> str:
    """
    Get text content from the system clipboard.

    Returns:
        str: The clipboard content as text

    Raises:
        ClipboardError: If clipboard access fails or no content is available
    """
    system = platform.system().lower()

    try:
        if system == "darwin":  # macOS
            return _get_clipboard_macos()
        elif system == "windows":  # Windows
            return _get_clipboard_windows()
        elif system == "linux":  # Linux
            return _get_clipboard_linux()
        else:
            raise ClipboardError(f"Unsupported platform: {system}")
    except subprocess.CalledProcessError as e:
        raise ClipboardError(f"Clipboard access failed: {e}")
    except FileNotFoundError as e:
        raise ClipboardError(f"Required clipboard utility not found: {e}")


def _get_clipboard_macos() -> str:
    """Get clipboard content on macOS using pbpaste."""
    result = subprocess.run(["pbpaste"], capture_output=True, text=True, check=True)
    return result.stdout


def _get_clipboard_windows() -> str:
    """Get clipboard content on Windows using PowerShell."""
    # Use PowerShell Get-Clipboard for better Unicode support
    result = subprocess.run(
        ["powershell", "-Command", "Get-Clipboard"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.rstrip("\r\n")


def _get_clipboard_linux() -> str:
    """Get clipboard content on Linux, with WSL detection."""
    # Check if we're in WSL
    if _is_wsl():
        return _get_clipboard_wsl()

    # Try standard Linux clipboard utilities in order of preference
    clipboard_commands = [
        ["xclip", "-selection", "clipboard", "-o"],
        ["xsel", "--clipboard", "--output"],
        ["wl-paste"],  # Wayland
    ]

    for cmd in clipboard_commands:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue

    raise ClipboardError(
        "No clipboard utility found. Please install xclip, xsel, or wl-clipboard"
    )


def _get_clipboard_wsl() -> str:
    """Get clipboard content in WSL environment using Windows clipboard."""
    try:
        # Try powershell.exe first (WSL2)
        result = subprocess.run(
            ["powershell.exe", "-Command", "Get-Clipboard"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.rstrip("\r\n")
    except FileNotFoundError:
        # Fallback to clip.exe
        try:
            # Note: clip.exe only sets clipboard, so we need to use another method
            # Try using /mnt/c/Windows/System32/clip.exe if available
            result = subprocess.run(
                [
                    "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe",
                    "-Command",
                    "Get-Clipboard",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.rstrip("\r\n")
        except (FileNotFoundError, subprocess.CalledProcessError):
            raise ClipboardError(
                "Cannot access Windows clipboard from WSL. "
                "Please ensure PowerShell is available."
            )


def _is_wsl() -> bool:
    """Check if running in Windows Subsystem for Linux."""
    try:
        # Check for WSL-specific indicators
        if os.path.exists("/proc/version"):
            with open("/proc/version", "r") as f:
                version_info = f.read().lower()
                return "microsoft" in version_info or "wsl" in version_info

        # Additional check for WSL environment variables
        return os.environ.get("WSL_DISTRO_NAME") is not None
    except Exception:
        return False


def is_clipboard_available() -> bool:
    """
    Check if clipboard functionality is available on this system.

    Returns:
        bool: True if clipboard can be accessed, False otherwise
    """
    try:
        get_clipboard_content()
        return True
    except ClipboardError:
        return False

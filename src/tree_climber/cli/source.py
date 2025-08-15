"""
Code source abstraction for handling input from files, clipboard, or stdin.
"""

import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class CodeSource(ABC):
    """Abstract base class for code sources (file or clipboard)."""

    @abstractmethod
    def get_content(self) -> str:
        """Get the source code content."""
        pass

    @abstractmethod
    def get_display_name(self) -> str:
        """Get a human-readable name for this source."""
        pass

    @abstractmethod
    def get_output_name(self) -> str:
        """Get a name suitable for output files (without spaces, etc.)."""
        pass

    @abstractmethod
    def get_language_hint(self) -> Optional[str]:
        """Get a language hint from file extension, if available."""
        pass

    @abstractmethod
    def get_output_dir(self) -> Path:
        """Get the default output directory for this source."""
        pass


class FileSource(CodeSource):
    """Code source from a file."""

    def __init__(self, file_path: Path):
        self.file_path = file_path

    def get_content(self) -> str:
        """Read content from the file."""
        if not self.file_path.is_file():
            raise ValueError(f"Not a file: {self.file_path}")
        return self.file_path.read_text(encoding="utf-8")

    def get_display_name(self) -> str:
        """Return the file path as display name."""
        return str(self.file_path)

    def get_output_name(self) -> str:
        """Return the file stem for output naming."""
        return self.file_path.name

    def get_language_hint(self) -> Optional[str]:
        """Auto-detect language from file extension."""
        suffix = self.file_path.suffix.lower()
        extension_map = {
            ".c": "c",
            ".h": "c",
            ".java": "java",
        }
        return extension_map.get(suffix)

    def get_output_dir(self) -> Path:
        """Return the parent directory of the file."""
        return self.file_path.parent if self.file_path.is_file() else self.file_path


class ClipboardSource(CodeSource):
    """Code source from clipboard."""

    def __init__(self, content: str):
        self.content = content

    def get_content(self) -> str:
        """Return the clipboard content."""
        return self.content

    def get_display_name(self) -> str:
        """Return a description for clipboard source."""
        return "clipboard"

    def get_output_name(self) -> str:
        """Return a generic name for clipboard output."""
        return "clipboard_code"

    def get_language_hint(self) -> Optional[str]:
        """Cannot detect language from clipboard content."""
        return None

    def get_output_dir(self) -> Path:
        """Return current working directory for clipboard sources."""
        return Path.cwd()


class StdinSource(CodeSource):
    """Code source from standard input (pipe)."""

    def __init__(self, content: str):
        self.content = content

    def get_content(self) -> str:
        """Return the stdin content."""
        return self.content

    def get_display_name(self) -> str:
        """Return a description for stdin source."""
        return "stdin"

    def get_output_name(self) -> str:
        """Return a generic name for stdin output."""
        return "stdin_code"

    def get_language_hint(self) -> Optional[str]:
        """Cannot detect language from stdin content."""
        return None

    def get_output_dir(self) -> Path:
        """Return current working directory for stdin sources."""
        return Path.cwd()


def is_stdin_available() -> bool:
    """Check if stdin has data available (is being piped to)."""
    return not sys.stdin.isatty()


def read_stdin() -> str:
    """Read all content from stdin."""
    return sys.stdin.read()

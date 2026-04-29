"""Parser for .env files — handles reading and tokenizing key-value pairs."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

_LINE_RE = re.compile(
    r"^\s*"
    r"(?P<key>[A-Za-z_][A-Za-z0-9_]*)"
    r"\s*=\s*"
    r"(?P<value>.*)$"
)


@dataclass
class EnvEntry:
    """Represents a single key=value pair from a .env file."""

    key: str
    value: str
    line_number: int
    raw: str

    def is_secret(self) -> bool:
        """Heuristic: treat entries whose keys contain SECRET/TOKEN/PASSWORD/KEY as secrets."""
        upper = self.key.upper()
        return any(word in upper for word in ("SECRET", "TOKEN", "PASSWORD", "KEY", "PRIVATE"))


@dataclass
class EnvFile:
    """Parsed representation of a .env file."""

    path: Optional[Path]
    entries: List[EnvEntry] = field(default_factory=list)

    @property
    def as_dict(self) -> Dict[str, str]:
        return {e.key: e.value for e in self.entries}

    def keys(self):
        return self.as_dict.keys()


def parse_env_string(text: str, source_path: Optional[Path] = None) -> EnvFile:
    """Parse a multi-line .env string and return an EnvFile."""
    entries: List[EnvEntry] = []

    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        stripped = raw_line.strip()

        # Skip blanks and comments
        if not stripped or stripped.startswith("#"):
            continue

        match = _LINE_RE.match(stripped)
        if not match:
            continue

        key = match.group("key")
        value = _strip_quotes(match.group("value").strip())
        entries.append(EnvEntry(key=key, value=value, line_number=lineno, raw=raw_line))

    return EnvFile(path=source_path, entries=entries)


def parse_env_file(path: Path) -> EnvFile:
    """Read a .env file from disk and parse it."""
    text = path.read_text(encoding="utf-8")
    return parse_env_string(text, source_path=path)


def _strip_quotes(value: str) -> str:
    """Remove surrounding single or double quotes from a value."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        return value[1:-1]
    return value

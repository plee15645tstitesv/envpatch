"""Scope filtering: restrict EnvFile views to a named prefix or group."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envpatch.parser import EnvEntry, EnvFile


@dataclass
class ScopeResult:
    """Result of scoping an EnvFile to a prefix."""
    prefix: str
    matched: List[EnvEntry] = field(default_factory=list)
    unmatched: List[EnvEntry] = field(default_factory=list)

    def ok(self) -> bool:
        return len(self.matched) > 0

    def as_env_file(self, strip_prefix: bool = True) -> EnvFile:
        """Return a new EnvFile containing only matched entries.

        If *strip_prefix* is True the scope prefix (and optional separator
        ``__``) is removed from each key so callers receive clean names.
        """
        entries: List[EnvEntry] = []
        sep = "__"
        for entry in self.matched:
            if strip_prefix and entry.key and entry.key.startswith(self.prefix + sep):
                stripped_key = entry.key[len(self.prefix) + len(sep):]
                entries.append(
                    EnvEntry(
                        key=stripped_key,
                        value=entry.value,
                        comment=entry.comment,
                        is_secret=entry.is_secret,
                    )
                )
            else:
                entries.append(entry)
        return EnvFile(entries=entries)


def scope(
    env: EnvFile,
    prefix: str,
    separator: str = "__",
    case_sensitive: bool = False,
) -> ScopeResult:
    """Partition *env* into entries whose key starts with *prefix* + *separator*.

    Args:
        env: Source ``EnvFile`` to filter.
        prefix: Scope name, e.g. ``"DB"`` to match ``DB__HOST``.
        separator: Delimiter between scope and key name (default ``"__"``).
        case_sensitive: When False (default) comparison is case-insensitive.

    Returns:
        A ``ScopeResult`` with matched / unmatched partitions.
    """
    full_prefix = prefix + separator
    matched: List[EnvEntry] = []
    unmatched: List[EnvEntry] = []

    for entry in env.entries:
        if entry.comment or entry.key is None:
            unmatched.append(entry)
            continue
        key = entry.key if case_sensitive else entry.key.upper()
        fp = full_prefix if case_sensitive else full_prefix.upper()
        if key.startswith(fp):
            matched.append(entry)
        else:
            unmatched.append(entry)

    return ScopeResult(prefix=prefix, matched=matched, unmatched=unmatched)

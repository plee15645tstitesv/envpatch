"""Sort entries in an .env file by key name, with options for grouping."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .parser import EnvEntry, EnvFile


@dataclass
class SortResult:
    source_env: str
    entries: List[EnvEntry] = field(default_factory=list)
    total_sorted: int = 0
    total_comments: int = 0

    def ok(self) -> bool:
        return True

    def as_env_file(self) -> EnvFile:
        return EnvFile(entries=self.entries)


def sort(
    env: EnvFile,
    *,
    source_env: str = "<unknown>",
    reverse: bool = False,
    group_by_prefix: bool = False,
    strip_comments: bool = False,
) -> SortResult:
    """Return a new EnvFile with key entries sorted alphabetically.

    Args:
        env: The source EnvFile to sort.
        source_env: Label used in the result for reporting.
        reverse: If True, sort in descending order.
        group_by_prefix: If True, group keys sharing the same ``PREFIX_`` together
            before sorting within each group.
        strip_comments: If True, omit comment/blank entries from the output.
    """
    comments = [e for e in env.entries if e.comment]
    key_entries = [e for e in env.entries if not e.comment]

    if group_by_prefix:
        def _prefix(e: EnvEntry) -> str:
            parts = e.key.split("_", 1) if e.key else [""]
            return parts[0].upper()

        key_entries = sorted(key_entries, key=lambda e: (_prefix(e), e.key or ""), reverse=reverse)
    else:
        key_entries = sorted(key_entries, key=lambda e: e.key or "", reverse=reverse)

    if strip_comments:
        result_entries = key_entries
    else:
        result_entries = comments + key_entries

    return SortResult(
        source_env=source_env,
        entries=result_entries,
        total_sorted=len(key_entries),
        total_comments=len(comments),
    )

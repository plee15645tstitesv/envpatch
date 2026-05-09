"""Trim .env files by removing unused, duplicate, or empty keys."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Set

from envpatch.parser import EnvEntry, EnvFile


@dataclass
class TrimResult:
    entries: List[EnvEntry] = field(default_factory=list)
    removed_empty: List[str] = field(default_factory=list)
    removed_duplicate: List[str] = field(default_factory=list)
    removed_unused: List[str] = field(default_factory=list)

    def ok(self) -> bool:
        return True

    def as_env_file(self) -> EnvFile:
        return EnvFile(entries=self.entries)

    @property
    def total_removed(self) -> int:
        return (
            len(self.removed_empty)
            + len(self.removed_duplicate)
            + len(self.removed_unused)
        )


def trim(
    env: EnvFile,
    *,
    remove_empty: bool = True,
    remove_duplicates: bool = True,
    keep_keys: Set[str] | None = None,
) -> TrimResult:
    """Return a TrimResult with unwanted entries stripped.

    Args:
        env: The source EnvFile to trim.
        remove_empty: Drop entries whose value is an empty string.
        remove_duplicates: When a key appears more than once keep only the
            last occurrence (matches shell semantics).
        keep_keys: If provided, any key *not* in this set is treated as
            unused and removed (comments are always kept).
    """
    result = TrimResult()

    # ---- duplicate pass (keep last occurrence) ----
    seen: dict[str, int] = {}
    for i, entry in enumerate(env.entries):
        if not entry.is_comment and entry.key:
            seen[entry.key] = i

    kept_entries: List[EnvEntry] = []
    duplicate_keys: List[str] = []
    for i, entry in enumerate(env.entries):
        if not entry.is_comment and entry.key and remove_duplicates:
            if seen[entry.key] != i:
                duplicate_keys.append(entry.key)
                continue
        kept_entries.append(entry)

    result.removed_duplicate = list(dict.fromkeys(duplicate_keys))

    # ---- empty + unused pass ----
    final_entries: List[EnvEntry] = []
    for entry in kept_entries:
        if entry.is_comment:
            final_entries.append(entry)
            continue
        if remove_empty and entry.value == "":
            result.removed_empty.append(entry.key)
            continue
        if keep_keys is not None and entry.key not in keep_keys:
            result.removed_unused.append(entry.key)
            continue
        final_entries.append(entry)

    result.entries = final_entries
    return result

"""Chain multiple .env files together with priority-based merging.

Later files in the chain take precedence over earlier ones, allowing
environment-specific overrides (e.g. base -> staging -> local).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .parser import EnvFile, EnvEntry
from .redact import redact_entry


@dataclass
class ChainResult:
    """Result of resolving a chain of env files."""
    entries: List[EnvEntry]
    source_map: dict  # key -> name of file that won
    chain_names: List[str]

    def ok(self) -> bool:
        return len(self.entries) > 0 or len(self.chain_names) > 0

    def as_env_file(self) -> EnvFile:
        return EnvFile(entries=self.entries)

    def total_keys(self) -> int:
        return sum(1 for e in self.entries if not e.comment and e.key)


def chain(
    files: List[EnvFile],
    names: Optional[List[str]] = None,
    include_comments: bool = False,
) -> ChainResult:
    """Merge a list of EnvFiles left-to-right, later files win.

    Args:
        files: Ordered list of EnvFile objects; last has highest priority.
        names: Optional labels for each file (used in source_map).
        include_comments: If True, comments from the highest-priority
                          file that defines a key are preserved.

    Returns:
        ChainResult with merged entries and provenance information.
    """
    if names is None:
        names = [f"file{i}" for i in range(len(files))]

    if len(names) != len(files):
        raise ValueError("names length must match files length")

    merged: dict[str, EnvEntry] = {}
    source_map: dict[str, str] = {}

    for file_obj, name in zip(files, names):
        for entry in file_obj.entries:
            if entry.comment or not entry.key:
                continue
            merged[entry.key] = entry
            source_map[entry.key] = name

    result_entries: List[EnvEntry] = []
    if include_comments:
        # Preserve comment entries from the last file only
        seen_keys: set[str] = set()
        for entry in reversed(files[-1].entries if files else []):
            if entry.comment:
                result_entries.insert(0, entry)
            elif entry.key and entry.key not in seen_keys:
                seen_keys.add(entry.key)

    for entry in merged.values():
        result_entries.append(entry)

    return ChainResult(
        entries=result_entries,
        source_map=source_map,
        chain_names=names,
    )

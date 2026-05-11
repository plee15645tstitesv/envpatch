"""Detect and remove duplicate keys within a single .env file."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envpatch.parser import EnvEntry, EnvFile


@dataclass
class DedupeResult:
    """Result of a deduplication pass over an EnvFile."""

    deduplicated: EnvFile
    duplicates: Dict[str, List[EnvEntry]] = field(default_factory=dict)

    def ok(self) -> bool:
        """True when no duplicate keys were found."""
        return len(self.duplicates) == 0

    @property
    def total_removed(self) -> int:
        """Total number of entries removed (all occurrences minus the kept one)."""
        return sum(len(v) - 1 for v in self.duplicates.values())

    @property
    def duplicate_keys(self) -> List[str]:
        return sorted(self.duplicates.keys())


def dedupe(
    env_file: EnvFile,
    *,
    keep: str = "last",
) -> DedupeResult:
    """Remove duplicate keys from *env_file*.

    Parameters
    ----------
    env_file:
        The source file to deduplicate.
    keep:
        ``"last"`` (default) keeps the final occurrence of each key;
        ``"first"`` keeps the first occurrence.
    """
    if keep not in ("first", "last"):
        raise ValueError(f"keep must be 'first' or 'last', got {keep!r}")

    seen: Dict[str, List[int]] = {}  # key -> list of indices in env_file.entries
    for idx, entry in enumerate(env_file.entries):
        if entry.is_comment or entry.key is None:
            continue
        seen.setdefault(entry.key, []).append(idx)

    duplicates: Dict[str, List[EnvEntry]] = {}
    removed_indices: set = set()

    for key, indices in seen.items():
        if len(indices) < 2:
            continue
        all_entries = [env_file.entries[i] for i in indices]
        duplicates[key] = all_entries
        # Decide which index to *keep*, remove the rest
        keep_idx = indices[-1] if keep == "last" else indices[0]
        for i in indices:
            if i != keep_idx:
                removed_indices.add(i)

    kept_entries = [
        entry
        for idx, entry in enumerate(env_file.entries)
        if idx not in removed_indices
    ]
    return DedupeResult(
        deduplicated=EnvFile(entries=kept_entries),
        duplicates=duplicates,
    )

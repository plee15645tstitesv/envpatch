"""Rename keys across an EnvFile, optionally in-place."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envpatch.parser import EnvEntry, EnvFile


@dataclass
class RenameResult:
    """Outcome of a rename operation."""

    entries: List[EnvEntry] = field(default_factory=list)
    renamed: Dict[str, str] = field(default_factory=dict)   # old_key -> new_key
    not_found: List[str] = field(default_factory=list)

    def ok(self) -> bool:
        """True when every requested key was found and renamed."""
        return len(self.not_found) == 0

    def as_env_file(self) -> EnvFile:
        return EnvFile(entries=self.entries)

    def total_renamed(self) -> int:
        return len(self.renamed)

    def total_not_found(self) -> int:
        return len(self.not_found)


def rename(
    source: EnvFile,
    mapping: Dict[str, str],
    *,
    error_on_missing: bool = False,
) -> RenameResult:
    """Return a new EnvFile with keys renamed according to *mapping*.

    Parameters
    ----------
    source:
        The file whose keys should be renamed.
    mapping:
        ``{old_key: new_key}`` pairs.
    error_on_missing:
        If *True* and a key in *mapping* is absent from *source*, raise
        ``KeyError``; otherwise record it in ``RenameResult.not_found``.
    """
    # Build a quick lookup of which old keys exist.
    existing_keys = {
        e.key for e in source.entries if not e.is_comment and e.key is not None
    }

    not_found: List[str] = []
    for old_key in mapping:
        if old_key not in existing_keys:
            if error_on_missing:
                raise KeyError(f"Key not found in source file: {old_key!r}")
            not_found.append(old_key)

    # Keys that will actually be renamed.
    effective: Dict[str, str] = {
        k: v for k, v in mapping.items() if k not in not_found
    }

    new_entries: List[EnvEntry] = []
    for entry in source.entries:
        if entry.is_comment or entry.key is None:
            new_entries.append(entry)
            continue

        if entry.key in effective:
            new_entries.append(
                EnvEntry(
                    key=effective[entry.key],
                    value=entry.value,
                    is_comment=entry.is_comment,
                    raw=None,  # raw line is now stale
                )
            )
        else:
            new_entries.append(entry)

    return RenameResult(
        entries=new_entries,
        renamed=effective,
        not_found=not_found,
    )

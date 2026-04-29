"""Merge two .env files, with configurable conflict resolution."""

from enum import Enum
from typing import Dict, List, Optional

from .parser import EnvEntry, EnvFile


class ConflictStrategy(str, Enum):
    """How to handle keys that exist in both base and patch with different values."""
    USE_BASE = "base"      # keep base value
    USE_PATCH = "patch"    # use patch value (default)
    ERROR = "error"        # raise an exception


class MergeConflictError(Exception):
    """Raised when a merge conflict is detected and strategy is ERROR."""
    def __init__(self, key: str, base_value: str, patch_value: str) -> None:
        super().__init__(
            f"Merge conflict on key '{key}': "
            f"base={base_value!r}, patch={patch_value!r}"
        )
        self.key = key
        self.base_value = base_value
        self.patch_value = patch_value


def merge(
    base: EnvFile,
    patch: EnvFile,
    strategy: ConflictStrategy = ConflictStrategy.USE_PATCH,
    add_missing: bool = True,
) -> EnvFile:
    """
    Merge *patch* into *base* and return a new EnvFile.

    - Keys only in base: always kept.
    - Keys only in patch: added when add_missing=True.
    - Keys in both with same value: kept as-is.
    - Keys in both with different values: resolved by *strategy*.
    """
    base_dict: Dict[str, EnvEntry] = {e.key: e for e in base.entries if e.key}
    patch_dict: Dict[str, EnvEntry] = {e.key: e for e in patch.entries if e.key}

    merged: List[EnvEntry] = []

    # Walk base entries preserving order and comments
    for entry in base.entries:
        if entry.key is None:
            merged.append(entry)  # preserve comments / blank lines
            continue

        if entry.key in patch_dict:
            patch_entry = patch_dict[entry.key]
            if entry.value == patch_entry.value:
                merged.append(entry)
            else:
                if strategy == ConflictStrategy.ERROR:
                    raise MergeConflictError(entry.key, entry.value or "", patch_entry.value or "")
                elif strategy == ConflictStrategy.USE_PATCH:
                    merged.append(patch_entry)
                else:  # USE_BASE
                    merged.append(entry)
        else:
            merged.append(entry)

    if add_missing:
        existing_keys = {e.key for e in base.entries if e.key}
        for entry in patch.entries:
            if entry.key and entry.key not in existing_keys:
                merged.append(entry)

    return EnvFile(entries=merged)

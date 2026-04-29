"""Diff two .env files, masking secret values to avoid leaking them."""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from .parser import EnvFile, is_secret


class ChangeType(str, Enum):
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


@dataclass
class DiffEntry:
    key: str
    change: ChangeType
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    masked: bool = False

    def display_old(self) -> Optional[str]:
        if self.masked and self.old_value is not None:
            return "***"
        return self.old_value

    def display_new(self) -> Optional[str]:
        if self.masked and self.new_value is not None:
            return "***"
        return self.new_value


def diff(base: EnvFile, target: EnvFile, mask_secrets: bool = True) -> List[DiffEntry]:
    """Return a list of DiffEntry objects describing changes from base to target."""
    base_dict = base.as_dict()
    target_dict = target.as_dict()
    all_keys = sorted(set(base_dict) | set(target_dict))

    entries: List[DiffEntry] = []
    for key in all_keys:
        secret = mask_secrets and is_secret(key)
        if key not in base_dict:
            entries.append(
                DiffEntry(key=key, change=ChangeType.ADDED,
                          new_value=target_dict[key], masked=secret)
            )
        elif key not in target_dict:
            entries.append(
                DiffEntry(key=key, change=ChangeType.REMOVED,
                          old_value=base_dict[key], masked=secret)
            )
        elif base_dict[key] != target_dict[key]:
            entries.append(
                DiffEntry(key=key, change=ChangeType.MODIFIED,
                          old_value=base_dict[key], new_value=target_dict[key],
                          masked=secret)
            )
        else:
            entries.append(
                DiffEntry(key=key, change=ChangeType.UNCHANGED,
                          old_value=base_dict[key], new_value=target_dict[key],
                          masked=secret)
            )
    return entries


def format_diff(entries: List[DiffEntry], show_unchanged: bool = False) -> str:
    """Render diff entries as a human-readable string."""
    lines: List[str] = []
    symbols = {
        ChangeType.ADDED: "+",
        ChangeType.REMOVED: "-",
        ChangeType.MODIFIED: "~",
        ChangeType.UNCHANGED: " ",
    }
    for entry in entries:
        if entry.change == ChangeType.UNCHANGED and not show_unchanged:
            continue
        sym = symbols[entry.change]
        if entry.change == ChangeType.MODIFIED:
            lines.append(f"{sym} {entry.key}: {entry.display_old()!r} -> {entry.display_new()!r}")
        elif entry.change == ChangeType.ADDED:
            lines.append(f"{sym} {entry.key}={entry.display_new()!r}")
        elif entry.change == ChangeType.REMOVED:
            lines.append(f"{sym} {entry.key}={entry.display_old()!r}")
        else:
            lines.append(f"{sym} {entry.key}={entry.display_new()!r}")
    return "\n".join(lines)

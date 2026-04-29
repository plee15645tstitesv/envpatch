"""Diff two EnvFile instances and report changes."""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from envpatch.parser import EnvFile
from envpatch.redact import redact_value


class ChangeType(str, Enum):
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


@dataclass
class DiffEntry:
    key: str
    change_type: ChangeType
    old_value: Optional[str] = None
    new_value: Optional[str] = None


def display_old(entry: DiffEntry, redact: bool = True) -> str:
    """Return the old value for display, optionally redacting secrets."""
    if entry.old_value is None:
        return ""
    if redact:
        return redact_value(entry.key, entry.old_value)
    return entry.old_value


def display_new(entry: DiffEntry, redact: bool = True) -> str:
    """Return the new value for display, optionally redacting secrets."""
    if entry.new_value is None:
        return ""
    if redact:
        return redact_value(entry.key, entry.new_value)
    return entry.new_value


def diff(base: EnvFile, other: EnvFile) -> List[DiffEntry]:
    """Compute the diff between two EnvFile instances.

    Returns a list of DiffEntry objects sorted by key.
    """
    base_dict = base.as_dict()
    other_dict = other.as_dict()

    all_keys = sorted(set(base_dict.keys()) | set(other_dict.keys()))
    results: List[DiffEntry] = []

    for key in all_keys:
        in_base = key in base_dict
        in_other = key in other_dict

        if in_base and not in_other:
            results.append(
                DiffEntry(key=key, change_type=ChangeType.REMOVED, old_value=base_dict[key])
            )
        elif not in_base and in_other:
            results.append(
                DiffEntry(key=key, change_type=ChangeType.ADDED, new_value=other_dict[key])
            )
        elif base_dict[key] != other_dict[key]:
            results.append(
                DiffEntry(
                    key=key,
                    change_type=ChangeType.MODIFIED,
                    old_value=base_dict[key],
                    new_value=other_dict[key],
                )
            )
        else:
            results.append(
                DiffEntry(
                    key=key,
                    change_type=ChangeType.UNCHANGED,
                    old_value=base_dict[key],
                    new_value=other_dict[key],
                )
            )

    return results


def format_diff(entries: List[DiffEntry], redact: bool = True) -> str:
    """Format a list of DiffEntry objects into a human-readable string."""
    lines = []
    symbols = {
        ChangeType.ADDED: "+",
        ChangeType.REMOVED: "-",
        ChangeType.MODIFIED: "~",
        ChangeType.UNCHANGED: " ",
    }
    for entry in entries:
        symbol = symbols[entry.change_type]
        if entry.change_type == ChangeType.MODIFIED:
            lines.append(f"{symbol} {entry.key}: {display_old(entry, redact)} -> {display_new(entry, redact)}")
        elif entry.change_type == ChangeType.ADDED:
            lines.append(f"{symbol} {entry.key}={display_new(entry, redact)}")
        elif entry.change_type == ChangeType.REMOVED:
            lines.append(f"{symbol} {entry.key}={display_old(entry, redact)}")
        else:
            lines.append(f"{symbol} {entry.key}={display_new(entry, redact)}")
    return "\n".join(lines)

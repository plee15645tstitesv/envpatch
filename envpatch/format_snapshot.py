"""Formatting helpers for snapshot-related CLI output."""

from __future__ import annotations

from pathlib import Path
from typing import List

from envpatch.snapshot import list_snapshots

_RESET = "\033[0m"
_BOLD = "\033[1m"
_CYAN = "\033[36m"
_YELLOW = "\033[33m"
_GREEN = "\033[32m"
_RED = "\033[31m"


def _colour(code: str, text: str, *, use_colour: bool = True) -> str:
    if not use_colour:
        return text
    return f"{code}{text}{_RESET}"


def format_snapshot_list(
    names: List[str],
    *,
    use_colour: bool = True,
) -> str:
    """Render a list of snapshot names for terminal display."""
    if not names:
        return _colour(_YELLOW, "(no snapshots saved)", use_colour=use_colour)
    lines = [_colour(_BOLD, "Saved snapshots:", use_colour=use_colour)]
    for name in names:
        lines.append("  " + _colour(_CYAN, name, use_colour=use_colour))
    return "\n".join(lines)


def format_snapshot_saved(
    name: str,
    path: Path,
    *,
    use_colour: bool = True,
) -> str:
    """Confirmation message after a snapshot is saved."""
    label = _colour(_GREEN, "Snapshot saved:", use_colour=use_colour)
    name_part = _colour(_CYAN, name, use_colour=use_colour)
    return f"{label} {name_part} → {path}"


def format_snapshot_deleted(
    name: str,
    *,
    use_colour: bool = True,
) -> str:
    """Confirmation message after a snapshot is deleted."""
    label = _colour(_RED, "Snapshot deleted:", use_colour=use_colour)
    name_part = _colour(_CYAN, name, use_colour=use_colour)
    return f"{label} {name_part}"


def format_snapshot_not_found(name: str, *, use_colour: bool = True) -> str:
    """Error message when a snapshot cannot be found."""
    return _colour(_RED, f"Error: snapshot '{name}' not found.", use_colour=use_colour)

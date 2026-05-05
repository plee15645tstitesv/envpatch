"""Formatting helpers for interpolation output."""

from __future__ import annotations

from envpatch.parser import EnvFile
from envpatch.interpolate import InterpolationError

_RESET = "\033[0m"
_RED = "\033[31m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_BOLD = "\033[1m"


def _c(code: str, text: str, colour: bool) -> str:
    return f"{code}{text}{_RESET}" if colour else text


def format_interpolated_file(
    original: EnvFile,
    resolved: EnvFile,
    colour: bool = False,
) -> str:
    """Show side-by-side original → resolved values for changed entries.

    Only lines where the value actually changed are printed; unchanged
    entries are omitted.  Returns an empty string when nothing changed.
    """
    lines: list[str] = []

    orig_map = {
        e.key: e.value
        for e in original.entries
        if e.key is not None and not e.is_comment
    }

    for entry in resolved.entries:
        if entry.is_comment or entry.key is None:
            continue
        old_val = orig_map.get(entry.key, "")
        new_val = entry.value or ""
        if old_val != new_val:
            key_str = _c(_BOLD, entry.key, colour)
            old_str = _c(_YELLOW, old_val, colour)
            new_str = _c(_GREEN, new_val, colour)
            lines.append(f"{key_str}: {old_str} → {new_str}")

    return "\n".join(lines)


def format_interpolation_error(err: InterpolationError, colour: bool = False) -> str:
    """Human-readable message for an unresolved variable reference."""
    label = _c(_RED, "InterpolationError", colour)
    key = _c(_BOLD, err.key, colour)
    ref = _c(_YELLOW, f"${err.ref}", colour)
    return f"{label}: key {key} references undefined variable {ref}"


def format_no_interpolation(colour: bool = False) -> str:
    """Message shown when no substitutions were performed."""
    msg = "No variable references found — file unchanged."
    return _c(_YELLOW, msg, colour)

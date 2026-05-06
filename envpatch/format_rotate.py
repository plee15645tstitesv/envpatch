"""Formatting helpers for key-rotation results."""
from __future__ import annotations

from .rotate import RotateResult


def _c(text: str, code: str, colour: bool) -> str:
    return f"\033[{code}m{text}\033[0m" if colour else text


def format_rotate_summary(result: RotateResult, *, colour: bool = False) -> str:
    """Return a human-readable summary line for a rotation result."""
    rotated = _c(str(result.total_rotated), "32", colour)
    skipped = _c(str(result.total_skipped), "33", colour)
    errors  = _c(str(len(result.errors)),   "31", colour)
    return (
        f"Rotation complete: {rotated} rotated, "
        f"{skipped} skipped, {errors} errors."
    )


def format_rotate_detail(result: RotateResult, *, colour: bool = False) -> str:
    """Return a multi-line detail view of which keys were affected."""
    lines: list[str] = []

    for key in result.rotated:
        lines.append(_c(f"  ✔ {key}", "32", colour))

    for key in result.skipped:
        lines.append(_c(f"  - {key} (not encrypted, skipped)", "33", colour))

    for key in result.errors:
        lines.append(_c(f"  ✘ {key} (error)", "31", colour))

    return "\n".join(lines) if lines else _c("  (no entries)", "90", colour)


def format_rotate_not_ok(result: RotateResult, *, colour: bool = False) -> str:
    """Return an error banner when rotation had failures."""
    msg = f"Rotation failed for {len(result.errors)} key(s): " + ", ".join(result.errors)
    return _c(msg, "31", colour)

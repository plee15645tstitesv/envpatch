"""Formatting helpers for mask results."""
from __future__ import annotations

from .mask import MaskResult

_ANSI_GREEN = "\033[32m"
_ANSI_YELLOW = "\033[33m"
_ANSI_RESET = "\033[0m"


def _c(text: str, code: str, colour: bool) -> str:
    return f"{code}{text}{_ANSI_RESET}" if colour else text


def format_mask_summary(result: MaskResult, *, colour: bool = False) -> str:
    """Return a one-line summary of the mask operation."""
    masked_str = _c(str(result.total_masked), _ANSI_YELLOW, colour)
    visible_str = _c(str(result.total_visible), _ANSI_GREEN, colour)
    return (
        f"Masked {masked_str} key(s), "
        f"{visible_str} key(s) left in plain text."
    )


def format_mask_entry(key: str, masked_value: str, *, colour: bool = False) -> str:
    """Return a display line for a single masked entry."""
    key_str = _c(key, _ANSI_YELLOW, colour)
    return f"  {key_str}={masked_value}"


def format_mask_output(
    result: MaskResult,
    *,
    colour: bool = False,
    show_all: bool = False,
) -> str:
    """Return a multi-line string representing the masked file contents.

    When *show_all* is ``False`` (default) only masked entries are listed.
    """
    lines: list[str] = [format_mask_summary(result, colour=colour)]
    for entry in result.entries:
        if entry.comment or entry.key is None:
            continue
        value = entry.value or ""
        is_masked = "*" in value
        if show_all or is_masked:
            lines.append(format_mask_entry(entry.key, value, colour=colour))
    return "\n".join(lines)

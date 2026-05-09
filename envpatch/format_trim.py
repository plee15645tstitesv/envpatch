"""Formatting helpers for TrimResult output."""
from __future__ import annotations

from envpatch.trim import TrimResult


def _c(text: str, code: str, *, colour: bool) -> str:
    return f"\033[{code}m{text}\033[0m" if colour else text


def format_trim_summary(result: TrimResult, *, colour: bool = False) -> str:
    """One-line summary of what was trimmed."""
    total = result.total_removed
    label = _c(f"{total} entr{'y' if total == 1 else 'ies'} removed", "33", colour=colour)
    parts = []
    if result.removed_empty:
        parts.append(f"{len(result.removed_empty)} empty")
    if result.removed_duplicate:
        parts.append(f"{len(result.removed_duplicate)} duplicate")
    if result.removed_unused:
        parts.append(f"{len(result.removed_unused)} unused")
    detail = f" ({', '.join(parts)})" if parts else ""
    return f"{label}{detail}"


def format_trim_detail(result: TrimResult, *, colour: bool = False) -> str:
    """Multi-line breakdown listing each removed key."""
    lines: list[str] = []

    def _section(title: str, keys: list[str], code: str) -> None:
        if not keys:
            return
        lines.append(_c(f"{title}:", "1", colour=colour))
        for k in keys:
            lines.append(f"  {_c('-', code, colour=colour)} {k}")

    _section("Empty", result.removed_empty, "33")
    _section("Duplicate", result.removed_duplicate, "35")
    _section("Unused", result.removed_unused, "31")

    if not lines:
        return _c("Nothing trimmed.", "2", colour=colour)
    return "\n".join(lines)


def format_trim_output(result: TrimResult, *, colour: bool = False) -> str:
    """Return the trimmed file rendered as a .env string."""
    from envpatch.format import format_env_file

    return format_env_file(result.as_env_file())

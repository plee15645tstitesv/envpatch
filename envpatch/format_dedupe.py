"""Formatters for DedupeResult output."""
from __future__ import annotations

from envpatch.dedupe import DedupeResult


def _c(text: str, code: str, *, colour: bool) -> str:
    return f"\033[{code}m{text}\033[0m" if colour else text


def format_dedupe_summary(result: DedupeResult, *, colour: bool = False) -> str:
    """One-line summary of the deduplication result."""
    if result.ok():
        msg = "No duplicate keys found."
        return _c(msg, "32", colour=colour)

    n_keys = len(result.duplicate_keys)
    n_removed = result.total_removed
    key_word = "key" if n_keys == 1 else "keys"
    entry_word = "entry" if n_removed == 1 else "entries"
    msg = f"Found {n_keys} duplicate {key_word}; removed {n_removed} {entry_word}."
    return _c(msg, "33", colour=colour)


def format_dedupe_detail(result: DedupeResult, *, colour: bool = False) -> str:
    """Per-key breakdown listing each duplicate key and its occurrence count."""
    if result.ok():
        return ""

    lines: list[str] = []
    for key in result.duplicate_keys:
        occurrences = len(result.duplicates[key])
        label = _c(key, "36", colour=colour)
        count_str = _c(str(occurrences), "33", colour=colour)
        lines.append(f"  {label}: {count_str} occurrences")
    return "\n".join(lines)


def format_dedupe_report(result: DedupeResult, *, colour: bool = False) -> str:
    """Full report combining summary and per-key detail."""
    summary = format_dedupe_summary(result, colour=colour)
    detail = format_dedupe_detail(result, colour=colour)
    if detail:
        return f"{summary}\n{detail}"
    return summary

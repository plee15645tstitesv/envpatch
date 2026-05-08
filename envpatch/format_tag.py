"""Formatting helpers for tag results."""
from __future__ import annotations

from typing import List

from envpatch.tag import TagResult


def _c(text: str, code: str, colour: bool) -> str:
    return f"\033[{code}m{text}\033[0m" if colour else text


def format_tag_summary(result: TagResult, *, colour: bool = False) -> str:
    """One-line summary: tagged / untagged counts."""
    tagged_str = _c(str(result.total_tagged()), "32", colour)
    untagged_str = _c(str(result.total_untagged()), "33", colour)
    return f"tagged: {tagged_str}  untagged: {untagged_str}"


def format_tag_detail(result: TagResult, *, colour: bool = False) -> str:
    """Per-key breakdown of assigned tags."""
    lines: List[str] = []
    for entry in result.tagged:
        label_str = ", ".join(sorted(entry.tags))
        key_part = _c(entry.key, "36", colour)
        tag_part = _c(label_str, "35", colour)
        lines.append(f"  {key_part}  [{tag_part}]")
    if result.untagged_keys:
        lines.append("")
        lines.append(_c("untagged:", "33", colour))
        for k in result.untagged_keys:
            lines.append(f"  {_c(k, '90', colour)}")
    return "\n".join(lines)


def format_tag_filter(
    tag: str, keys: List[str], *, colour: bool = False
) -> str:
    """Display the keys that matched a given tag filter."""
    header = _c(f"Keys tagged '{tag}':", "1", colour)
    if not keys:
        return f"{header}\n  {_c('(none)', '90', colour)}"
    body = "\n".join(f"  {_c(k, '36', colour)}" for k in keys)
    return f"{header}\n{body}"

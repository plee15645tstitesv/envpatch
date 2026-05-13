"""Formatting helpers for sort results."""
from __future__ import annotations

from .sort import SortResult


def _c(text: str, code: str, colour: bool) -> str:
    return f"\033[{code}m{text}\033[0m" if colour else text


def format_sort_header(result: SortResult, *, colour: bool = False) -> str:
    env = _c(result.source_env, "36", colour)
    return f"Sorted: {env}"


def format_sort_summary(result: SortResult, *, colour: bool = False) -> str:
    sorted_label = _c(str(result.total_sorted), "32", colour)
    comment_label = _c(str(result.total_comments), "33", colour)
    lines = [
        f"  Keys sorted : {sorted_label}",
        f"  Comments    : {comment_label}",
    ]
    return "\n".join(lines)


def format_sort_output(result: SortResult, *, colour: bool = False) -> str:
    from .format import format_env_file  # avoid circular at module level

    header = format_sort_header(result, colour=colour)
    summary = format_sort_summary(result, colour=colour)
    body = format_env_file(result.as_env_file())
    return "\n".join([header, summary, "", body])

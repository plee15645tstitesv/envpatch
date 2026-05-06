"""Formatting helpers for watch events."""

from __future__ import annotations

from envpatch.watch import WatchEvent
from envpatch.format import format_diff


def _c(text: str, code: str, colour: bool) -> str:
    return f"\033[{code}m{text}\033[0m" if colour else text


def format_watch_header(event: WatchEvent, colour: bool = False) -> str:
    """Return a one-line header describing a watch event."""
    path_str = _c(str(event.path), "36", colour)
    count = len(event.changes)
    noun = "change" if count == 1 else "changes"
    count_str = _c(str(count), "33", colour)
    return f"[watch] {path_str} — {count_str} {noun} detected"


def format_watch_no_changes(event: WatchEvent, colour: bool = False) -> str:
    """Return a message when a file was touched but no keys changed."""
    path_str = _c(str(event.path), "36", colour)
    return f"[watch] {path_str} — file modified, no key changes"


def format_watch_event(
    event: WatchEvent,
    redact: bool = True,
    colour: bool = False,
) -> str:
    """Return a full formatted string for a watch event."""
    if not event.has_changes:
        return format_watch_no_changes(event, colour=colour)

    lines = [format_watch_header(event, colour=colour)]
    diff_text = format_diff(event.changes, redact=redact, colour=colour)
    if diff_text:
        lines.append(diff_text)
    return "\n".join(lines)

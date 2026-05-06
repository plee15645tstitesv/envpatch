"""Tests for envpatch.format_watch."""

from __future__ import annotations

from pathlib import Path

from envpatch.parser import EnvFile
from envpatch.watch import WatchEvent
from envpatch.diff import diff
from envpatch.format_watch import (
    format_watch_header,
    format_watch_no_changes,
    format_watch_event,
)


def _make(text: str) -> EnvFile:
    return EnvFile.parse(text)


def _event(prev_text: str, curr_text: str, path: str = ".env") -> WatchEvent:
    prev = _make(prev_text)
    curr = _make(curr_text)
    changes = diff(prev, curr)
    return WatchEvent(path=Path(path), previous=prev, current=curr, changes=changes)


def test_header_contains_path():
    event = _event("A=1", "A=2")
    result = format_watch_header(event)
    assert ".env" in result


def test_header_contains_change_count():
    event = _event("A=1\nB=2", "A=9\nB=2")
    result = format_watch_header(event)
    assert "1 change" in result


def test_header_plural_changes():
    event = _event("A=1\nB=2", "A=9\nB=8")
    result = format_watch_header(event)
    assert "2 changes" in result


def test_no_changes_message():
    prev = _make("A=1")
    event = WatchEvent(path=Path(".env"), previous=prev, current=prev, changes=[])
    result = format_watch_no_changes(event)
    assert "no key changes" in result


def test_format_event_with_changes():
    event = _event("A=1", "A=2")
    result = format_watch_event(event)
    assert "[watch]" in result
    assert ".env" in result


def test_format_event_no_changes_returns_no_changes_msg():
    prev = _make("A=1")
    event = WatchEvent(path=Path(".env"), previous=prev, current=prev, changes=[])
    result = format_watch_event(event)
    assert "no key changes" in result


def test_format_event_colour_contains_ansi():
    event = _event("A=1", "A=2")
    result = format_watch_event(event, colour=True)
    assert "\033[" in result


def test_format_event_no_colour_no_ansi():
    event = _event("A=1", "A=2")
    result = format_watch_event(event, colour=False)
    assert "\033[" not in result

"""Tests for envpatch.watch."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from envpatch.parser import EnvFile
from envpatch.watch import FileWatcher, WatchEvent
from envpatch.diff import ChangeType


def _make(text: str) -> EnvFile:
    return EnvFile.parse(text)


# ---------------------------------------------------------------------------
# WatchEvent
# ---------------------------------------------------------------------------

def test_watch_event_has_changes_true():
    prev = _make("A=1")
    curr = _make("A=2")
    from envpatch.diff import diff
    changes = diff(prev, curr)
    event = WatchEvent(path=Path(".env"), previous=prev, current=curr, changes=changes)
    assert event.has_changes is True


def test_watch_event_has_changes_false():
    prev = _make("A=1")
    curr = _make("A=1")
    event = WatchEvent(path=Path(".env"), previous=prev, current=curr, changes=[])
    assert event.has_changes is False


# ---------------------------------------------------------------------------
# FileWatcher — polling logic
# ---------------------------------------------------------------------------

def test_watcher_detects_modification(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\n")

    events: list[WatchEvent] = []

    def on_change(event: WatchEvent) -> None:
        events.append(event)

    watcher = FileWatcher(env_file, on_change, interval=0)
    # prime internal state
    watcher._check()

    # modify the file with a clearly different mtime
    time.sleep(0.01)
    env_file.write_text("FOO=baz\n")
    import os
    os.utime(env_file, (time.time() + 1, time.time() + 1))

    watcher._check()

    assert len(events) == 1
    assert events[0].has_changes is True


def test_watcher_no_event_when_unchanged(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\n")

    events: list[WatchEvent] = []
    watcher = FileWatcher(env_file, lambda e: events.append(e), interval=0)
    watcher._check()
    watcher._check()

    assert events == []


def test_watcher_missing_file_does_not_raise(tmp_path):
    env_file = tmp_path / "missing.env"
    watcher = FileWatcher(env_file, lambda e: None, interval=0)
    watcher._check()  # should not raise


def test_watcher_start_max_iterations(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("X=1\n")

    call_count = 0

    def on_change(event: WatchEvent) -> None:
        nonlocal call_count
        call_count += 1

    watcher = FileWatcher(env_file, on_change, interval=0)
    watcher.start(max_iterations=3)
    # No crash; internal state initialised
    assert watcher._last_file is not None


def test_watcher_change_type_is_modified(tmp_path):
    import os
    env_file = tmp_path / ".env"
    env_file.write_text("SECRET_KEY=old\n")

    events: list[WatchEvent] = []
    watcher = FileWatcher(env_file, lambda e: events.append(e), interval=0)
    watcher._check()

    env_file.write_text("SECRET_KEY=new\n")
    os.utime(env_file, (time.time() + 2, time.time() + 2))
    watcher._check()

    assert events[0].changes[0].change == ChangeType.MODIFIED

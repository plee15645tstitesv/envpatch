"""Tests for envpatch.pin."""
from __future__ import annotations

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.pin import PinEntry, PinResult, apply_pins


def _entry(key: str, value: str) -> EnvEntry:
    return EnvEntry(key=key, value=value, comment=False, is_comment=False)


def _comment(text: str) -> EnvEntry:
    return EnvEntry(key=None, value=None, comment=True, is_comment=True)


def _file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


# ---------------------------------------------------------------------------
# PinEntry
# ---------------------------------------------------------------------------

def test_pin_entry_as_dict_without_reason():
    pe = PinEntry(key="FOO", value="bar")
    d = pe.as_dict()
    assert d == {"key": "FOO", "value": "bar"}
    assert "reason" not in d


def test_pin_entry_as_dict_with_reason():
    pe = PinEntry(key="FOO", value="bar", reason="locked for prod")
    d = pe.as_dict()
    assert d["reason"] == "locked for prod"


# ---------------------------------------------------------------------------
# PinResult
# ---------------------------------------------------------------------------

def test_result_ok_always_true():
    assert PinResult().ok is True


def test_result_total_counts():
    r = PinResult(pinned=["A", "B"], skipped=["C"])
    assert r.total_pinned == 2
    assert r.total_skipped == 1


# ---------------------------------------------------------------------------
# apply_pins – overwrite=True (default)
# ---------------------------------------------------------------------------

def test_apply_pins_overwrites_existing_key():
    env = _file(_entry("HOST", "localhost"), _entry("PORT", "5432"))
    pins = {"HOST": PinEntry(key="HOST", value="prod.example.com")}
    result = apply_pins(env, pins)
    assert result.ok
    assert "HOST" in result.pinned
    values = {e.key: e.value for e in result.file.entries if e.key}
    assert values["HOST"] == "prod.example.com"
    assert values["PORT"] == "5432"


def test_apply_pins_adds_missing_key():
    env = _file(_entry("PORT", "5432"))
    pins = {"NEW_KEY": PinEntry(key="NEW_KEY", value="42")}
    result = apply_pins(env, pins)
    assert "NEW_KEY" in result.pinned
    keys = [e.key for e in result.file.entries if e.key]
    assert "NEW_KEY" in keys


def test_apply_pins_multiple_pins():
    env = _file(_entry("A", "1"), _entry("B", "2"))
    pins = {
        "A": PinEntry(key="A", value="pinned_a"),
        "C": PinEntry(key="C", value="pinned_c"),
    }
    result = apply_pins(env, pins)
    assert set(result.pinned) == {"A", "C"}
    assert result.total_skipped == 0


# ---------------------------------------------------------------------------
# apply_pins – overwrite=False
# ---------------------------------------------------------------------------

def test_apply_pins_skips_existing_when_overwrite_false():
    env = _file(_entry("HOST", "localhost"))
    pins = {"HOST": PinEntry(key="HOST", value="prod.example.com")}
    result = apply_pins(env, pins, overwrite=False)
    assert "HOST" in result.skipped
    assert "HOST" not in result.pinned
    values = {e.key: e.value for e in result.file.entries if e.key}
    assert values["HOST"] == "localhost"


def test_apply_pins_adds_new_key_when_overwrite_false():
    env = _file(_entry("A", "1"))
    pins = {"B": PinEntry(key="B", value="2")}
    result = apply_pins(env, pins, overwrite=False)
    assert "B" in result.pinned
    assert result.total_skipped == 0


def test_apply_pins_preserves_comments():
    env = _file(_comment("# header"), _entry("X", "old"))
    pins = {"X": PinEntry(key="X", value="new")}
    result = apply_pins(env, pins)
    comment_entries = [e for e in result.file.entries if e.is_comment]
    assert len(comment_entries) == 1

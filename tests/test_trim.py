"""Tests for envpatch.trim."""
from __future__ import annotations

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.trim import trim


def _entry(key: str, value: str = "val", *, secret: bool = False) -> EnvEntry:
    return EnvEntry(key=key, value=value, raw=f"{key}={value}", is_comment=False, is_secret=secret)


def _comment(text: str = "# note") -> EnvEntry:
    return EnvEntry(key="", value="", raw=text, is_comment=True, is_secret=False)


def _file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


def test_trim_returns_result():
    result = trim(_file(_entry("A")))
    assert result.ok()


def test_trim_removes_empty_value_by_default():
    result = trim(_file(_entry("A", ""), _entry("B", "hello")))
    keys = [e.key for e in result.entries if not e.is_comment]
    assert "A" not in keys
    assert "B" in keys
    assert "A" in result.removed_empty


def test_trim_keeps_empty_when_disabled():
    result = trim(_file(_entry("A", "")), remove_empty=False)
    keys = [e.key for e in result.entries if not e.is_comment]
    assert "A" in keys
    assert result.removed_empty == []


def test_trim_removes_duplicate_keeps_last():
    e1 = _entry("DB", "old")
    e2 = _entry("DB", "new")
    result = trim(_file(e1, e2))
    surviving = [e for e in result.entries if not e.is_comment]
    assert len(surviving) == 1
    assert surviving[0].value == "new"
    assert "DB" in result.removed_duplicate


def test_trim_duplicate_disabled_keeps_both():
    e1 = _entry("DB", "old")
    e2 = _entry("DB", "new")
    result = trim(_file(e1, e2), remove_duplicates=False)
    surviving = [e for e in result.entries if not e.is_comment]
    assert len(surviving) == 2
    assert result.removed_duplicate == []


def test_trim_removes_unused_keys():
    result = trim(_file(_entry("A"), _entry("B"), _entry("C")), keep_keys={"A"})
    keys = [e.key for e in result.entries if not e.is_comment]
    assert keys == ["A"]
    assert set(result.removed_unused) == {"B", "C"}


def test_trim_keep_keys_none_keeps_all():
    result = trim(_file(_entry("A"), _entry("B")), keep_keys=None)
    keys = [e.key for e in result.entries if not e.is_comment]
    assert set(keys) == {"A", "B"}
    assert result.removed_unused == []


def test_trim_preserves_comments():
    result = trim(_file(_comment("# section"), _entry("A", "")))
    comments = [e for e in result.entries if e.is_comment]
    assert len(comments) == 1


def test_trim_total_removed_sums_all_categories():
    result = trim(
        _file(_entry("A", ""), _entry("B"), _entry("B", "v2")),
        keep_keys={"B"},
    )
    # A removed (empty), first B removed (duplicate)
    assert result.total_removed == 2


def test_trim_as_env_file_returns_env_file():
    result = trim(_file(_entry("A"), _entry("B", "")))
    env = result.as_env_file()
    assert hasattr(env, "entries")

"""Tests for envpatch.tag."""
from __future__ import annotations

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.tag import TagEntry, TagResult, tag


def _entry(key: str, value: str = "val", secret: bool = False) -> EnvEntry:
    return EnvEntry(key=key, raw_value=value, comment=False, secret=secret)


def _comment() -> EnvEntry:
    return EnvEntry(key="", raw_value="# comment", comment=True, secret=False)


def _file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


# ---------------------------------------------------------------------------
# TagEntry
# ---------------------------------------------------------------------------

def test_tag_entry_as_dict_sorted_tags():
    e = TagEntry(key="FOO", tags=["z", "a", "m"])
    assert e.as_dict() == {"key": "FOO", "tags": ["a", "m", "z"]}


# ---------------------------------------------------------------------------
# tag()
# ---------------------------------------------------------------------------

def test_tag_assigns_label_to_matching_key():
    f = _file(_entry("DB_HOST"), _entry("APP_NAME"))
    result = tag(f, {"database": ["DB_HOST"]})
    assert result.total_tagged() == 1
    assert result.tagged[0].key == "DB_HOST"
    assert "database" in result.tagged[0].tags


def test_tag_unmatched_key_in_untagged():
    f = _file(_entry("DB_HOST"), _entry("APP_NAME"))
    result = tag(f, {"database": ["DB_HOST"]})
    assert "APP_NAME" in result.untagged_keys


def test_tag_multiple_labels_for_same_key():
    f = _file(_entry("SECRET_KEY"))
    result = tag(f, {"auth": ["SECRET_KEY"], "critical": ["SECRET_KEY"]})
    assert result.total_tagged() == 1
    tags = result.tagged[0].tags
    assert "auth" in tags
    assert "critical" in tags


def test_tag_comments_are_ignored():
    f = _file(_comment(), _entry("FOO"))
    result = tag(f, {"misc": ["FOO"]})
    assert result.total_tagged() == 1
    assert result.total_untagged() == 0


def test_tag_empty_map_all_untagged():
    f = _file(_entry("A"), _entry("B"))
    result = tag(f, {})
    assert result.total_tagged() == 0
    assert set(result.untagged_keys) == {"A", "B"}


def test_tag_result_ok_always_true():
    result = tag(_file(_entry("X")), {})
    assert result.ok() is True


def test_keys_for_tag_returns_correct_keys():
    f = _file(_entry("A"), _entry("B"), _entry("C"))
    result = tag(f, {"group1": ["A", "C"], "group2": ["B"]})
    assert set(result.keys_for_tag("group1")) == {"A", "C"}
    assert result.keys_for_tag("group2") == ["B"]


def test_keys_for_missing_tag_returns_empty():
    f = _file(_entry("A"))
    result = tag(f, {"x": ["A"]})
    assert result.keys_for_tag("nonexistent") == []


def test_as_env_file_filters_by_tag():
    f = _file(_entry("DB_HOST"), _entry("APP_NAME"), _entry("DB_PORT"))
    result = tag(f, {"db": ["DB_HOST", "DB_PORT"]})
    filtered = result.as_env_file("db", f)
    keys = [e.key for e in filtered.entries]
    assert set(keys) == {"DB_HOST", "DB_PORT"}
    assert "APP_NAME" not in keys

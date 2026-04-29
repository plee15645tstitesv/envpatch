"""Tests for envpatch.diff module."""

import pytest

from envpatch.diff import ChangeType, DiffEntry, diff, format_diff
from envpatch.parser import EnvFile


def _make(text: str) -> EnvFile:
    return EnvFile.parse(text)


def test_diff_added_key():
    base = _make("FOO=bar")
    target = _make("FOO=bar\nBAZ=qux")
    entries = diff(base, target, mask_secrets=False)
    added = [e for e in entries if e.change == ChangeType.ADDED]
    assert len(added) == 1
    assert added[0].key == "BAZ"
    assert added[0].new_value == "qux"


def test_diff_removed_key():
    base = _make("FOO=bar\nBAZ=qux")
    target = _make("FOO=bar")
    entries = diff(base, target, mask_secrets=False)
    removed = [e for e in entries if e.change == ChangeType.REMOVED]
    assert len(removed) == 1
    assert removed[0].key == "BAZ"
    assert removed[0].old_value == "qux"


def test_diff_modified_key():
    base = _make("FOO=bar")
    target = _make("FOO=baz")
    entries = diff(base, target, mask_secrets=False)
    modified = [e for e in entries if e.change == ChangeType.MODIFIED]
    assert len(modified) == 1
    assert modified[0].old_value == "bar"
    assert modified[0].new_value == "baz"


def test_diff_unchanged_key():
    base = _make("FOO=bar")
    target = _make("FOO=bar")
    entries = diff(base, target, mask_secrets=False)
    assert entries[0].change == ChangeType.UNCHANGED


def test_secret_values_masked():
    base = _make("SECRET_KEY=abc123")
    target = _make("SECRET_KEY=xyz789")
    entries = diff(base, target, mask_secrets=True)
    assert entries[0].masked is True
    assert entries[0].display_old() == "***"
    assert entries[0].display_new() == "***"


def test_secret_not_masked_when_disabled():
    base = _make("SECRET_KEY=abc123")
    target = _make("SECRET_KEY=xyz789")
    entries = diff(base, target, mask_secrets=False)
    assert entries[0].masked is False
    assert entries[0].display_old() == "abc123"


def test_format_diff_excludes_unchanged_by_default():
    base = _make("FOO=bar\nBAZ=old")
    target = _make("FOO=bar\nBAZ=new")
    entries = diff(base, target, mask_secrets=False)
    output = format_diff(entries)
    assert "FOO" not in output
    assert "BAZ" in output


def test_format_diff_includes_unchanged_when_requested():
    base = _make("FOO=bar")
    target = _make("FOO=bar")
    entries = diff(base, target, mask_secrets=False)
    output = format_diff(entries, show_unchanged=True)
    assert "FOO" in output


def test_diff_sorted_keys():
    base = _make("Z=1\nA=2")
    target = _make("Z=1\nA=2")
    entries = diff(base, target, mask_secrets=False)
    assert [e.key for e in entries] == ["A", "Z"]

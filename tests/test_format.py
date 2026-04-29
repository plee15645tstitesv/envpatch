"""Tests for envpatch.format module."""

import pytest
from envpatch.diff import DiffEntry, ChangeType
from envpatch.parser import EnvEntry, EnvFile
from envpatch.format import format_diff, format_env_file, _prefix


def _entry(key, value="val", secret=False):
    return EnvEntry(key=key, value=value, raw=f"{key}={value}", is_secret=secret)


def _diff(change_type, key, old=None, new=None):
    old_e = _entry(key, old) if old is not None else None
    new_e = _entry(key, new) if new is not None else None
    return DiffEntry(change_type=change_type, key=key, old_entry=old_e, new_entry=new_e)


class TestPrefix:
    def test_added(self):
        assert _prefix(ChangeType.ADDED) == "+"

    def test_removed(self):
        assert _prefix(ChangeType.REMOVED) == "-"

    def test_modified(self):
        assert _prefix(ChangeType.MODIFIED) == "~"

    def test_unchanged(self):
        assert _prefix(ChangeType.UNCHANGED) == " "


class TestFormatDiff:
    def test_added_entry_no_color(self):
        d = _diff(ChangeType.ADDED, "FOO", new="bar")
        result = format_diff([d], color=False)
        assert result == "+ FOO=bar"

    def test_removed_entry_no_color(self):
        d = _diff(ChangeType.REMOVED, "FOO", old="bar")
        result = format_diff([d], color=False)
        assert result == "- FOO=bar"

    def test_unchanged_entry_no_color(self):
        d = _diff(ChangeType.UNCHANGED, "FOO", new="bar")
        result = format_diff([d], color=False)
        assert result == "  FOO=bar"

    def test_modified_produces_two_lines(self):
        d = _diff(ChangeType.MODIFIED, "FOO", old="old", new="new")
        result = format_diff([d], color=False)
        lines = result.splitlines()
        assert len(lines) == 2
        assert lines[0] == "- FOO=old"
        assert lines[1] == "+ FOO=new"

    def test_color_added_contains_green(self):
        d = _diff(ChangeType.ADDED, "FOO", new="bar")
        result = format_diff([d], color=True)
        assert "\033[32m" in result

    def test_color_removed_contains_red(self):
        d = _diff(ChangeType.REMOVED, "FOO", old="bar")
        result = format_diff([d], color=True)
        assert "\033[31m" in result

    def test_redact_secret_value(self):
        old_e = EnvEntry(key="SECRET_KEY", value="mysecret", raw="SECRET_KEY=mysecret", is_secret=True)
        d = DiffEntry(change_type=ChangeType.ADDED, key="SECRET_KEY", old_entry=None, new_entry=old_e)
        result = format_diff([d], color=False, redact=True)
        assert "mysecret" not in result
        assert "SECRET_KEY" in result

    def test_multiple_entries(self):
        entries = [
            _diff(ChangeType.ADDED, "A", new="1"),
            _diff(ChangeType.REMOVED, "B", old="2"),
        ]
        result = format_diff(entries, color=False)
        lines = result.splitlines()
        assert len(lines) == 2


class TestFormatEnvFile:
    def test_basic_roundtrip(self):
        entries = [
            EnvEntry(key="FOO", value="bar", raw="FOO=bar", is_secret=False),
            EnvEntry(key="BAZ", value="qux", raw="BAZ=qux", is_secret=False),
        ]
        env = EnvFile(entries=entries, path="test.env")
        result = format_env_file(env)
        assert "FOO=bar" in result
        assert "BAZ=qux" in result

    def test_comment_preserved(self):
        entries = [
            EnvEntry(key=None, value=None, raw="# a comment", is_secret=False, comment="# a comment"),
            EnvEntry(key="FOO", value="bar", raw="FOO=bar", is_secret=False),
        ]
        env = EnvFile(entries=entries, path="test.env")
        result = format_env_file(env)
        assert "# a comment" in result

    def test_redact_secrets_in_format(self):
        entries = [
            EnvEntry(key="DB_PASSWORD", value="s3cr3t", raw="DB_PASSWORD=s3cr3t", is_secret=True),
        ]
        env = EnvFile(entries=entries, path="test.env")
        result = format_env_file(env, redact=True)
        assert "s3cr3t" not in result

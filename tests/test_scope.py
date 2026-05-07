"""Tests for envpatch.scope and envpatch.format_scope."""
from __future__ import annotations

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.scope import ScopeResult, scope
from envpatch.format_scope import (
    format_scope_header,
    format_scope_not_found,
    format_scope_summary,
)


def _entry(key: str, value: str = "val", secret: bool = False) -> EnvEntry:
    return EnvEntry(key=key, value=value, comment=False, is_secret=secret)


def _comment() -> EnvEntry:
    return EnvEntry(key=None, value="# a comment", comment=True, is_secret=False)


def _file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


# ---------------------------------------------------------------------------
# scope()
# ---------------------------------------------------------------------------

def test_scope_matches_prefixed_keys():
    f = _file(_entry("DB__HOST", "localhost"), _entry("APP_NAME", "myapp"))
    result = scope(f, "DB")
    assert len(result.matched) == 1
    assert result.matched[0].key == "DB__HOST"


def test_scope_unmatched_contains_rest():
    f = _file(_entry("DB__HOST"), _entry("APP_NAME"))
    result = scope(f, "DB")
    assert len(result.unmatched) == 1
    assert result.unmatched[0].key == "APP_NAME"


def test_scope_comments_go_to_unmatched():
    f = _file(_comment(), _entry("DB__PORT", "5432"))
    result = scope(f, "DB")
    assert len(result.unmatched) == 1
    assert result.unmatched[0].comment is True


def test_scope_ok_false_when_no_match():
    f = _file(_entry("APP_NAME", "x"))
    result = scope(f, "DB")
    assert result.ok() is False


def test_scope_ok_true_when_match():
    f = _file(_entry("DB__HOST", "localhost"))
    result = scope(f, "DB")
    assert result.ok() is True


def test_scope_case_insensitive_by_default():
    f = _file(_entry("db__host", "localhost"))
    result = scope(f, "DB")
    assert len(result.matched) == 1


def test_scope_case_sensitive_no_match():
    f = _file(_entry("db__host", "localhost"))
    result = scope(f, "DB", case_sensitive=True)
    assert len(result.matched) == 0


def test_scope_as_env_file_strips_prefix():
    f = _file(_entry("DB__HOST", "localhost"), _entry("DB__PORT", "5432"))
    result = scope(f, "DB")
    stripped = result.as_env_file(strip_prefix=True)
    keys = [e.key for e in stripped.entries]
    assert "HOST" in keys
    assert "PORT" in keys


def test_scope_as_env_file_keeps_prefix_when_false():
    f = _file(_entry("DB__HOST", "localhost"))
    result = scope(f, "DB")
    kept = result.as_env_file(strip_prefix=False)
    assert kept.entries[0].key == "DB__HOST"


# ---------------------------------------------------------------------------
# format helpers
# ---------------------------------------------------------------------------

def test_format_scope_header_contains_prefix():
    result = ScopeResult(prefix="DB", matched=[_entry("DB__HOST")], unmatched=[])
    out = format_scope_header(result, colour=False)
    assert "DB" in out
    assert "1" in out


def test_format_scope_summary_no_match():
    result = ScopeResult(prefix="DB", matched=[], unmatched=[])
    out = format_scope_summary(result, colour=False)
    assert "no keys matched" in out


def test_format_scope_summary_lists_keys():
    result = ScopeResult(prefix="DB", matched=[_entry("DB__HOST", "localhost")], unmatched=[])
    out = format_scope_summary(result, colour=False)
    assert "DB__HOST" in out


def test_format_scope_summary_with_colour_contains_ansi():
    result = ScopeResult(prefix="DB", matched=[_entry("DB__HOST")], unmatched=[])
    out = format_scope_summary(result, colour=True)
    assert "\033[" in out


def test_format_scope_not_found_contains_prefix():
    out = format_scope_not_found("REDIS", colour=False)
    assert "REDIS" in out

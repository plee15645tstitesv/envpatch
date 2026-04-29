"""Tests for envpatch.validate."""

from __future__ import annotations

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.validate import (
    ValidationIssue,
    ValidationResult,
    validate_file,
)


def _entry(key: str, value: str = "val", line_number: int = 1) -> EnvEntry:
    return EnvEntry(
        key=key,
        value=value,
        raw=f"{key}={value}",
        comment=False,
        blank=False,
        line_number=line_number,
    )


def _file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries), path=None)


# ---------------------------------------------------------------------------
# ValidationResult helpers
# ---------------------------------------------------------------------------

def test_result_ok_when_no_issues():
    r = ValidationResult()
    assert r.ok is True


def test_result_not_ok_when_error_present():
    r = ValidationResult(issues=[
        ValidationIssue(1, "K", "bad", "error")
    ])
    assert r.ok is False


def test_result_ok_with_only_warnings():
    r = ValidationResult(issues=[
        ValidationIssue(1, "K", "empty value", "warning")
    ])
    assert r.ok is True


def test_result_str_no_issues():
    assert "passed" in str(ValidationResult())


def test_result_str_with_issues():
    r = ValidationResult(issues=[ValidationIssue(3, "FOO", "duplicate key", "error")])
    text = str(r)
    assert "ERROR" in text
    assert "FOO" in text


# ---------------------------------------------------------------------------
# validate_file
# ---------------------------------------------------------------------------

def test_validate_clean_file():
    f = _file(_entry("A", "1", 1), _entry("B", "2", 2))
    result = validate_file(f)
    assert result.ok
    assert result.issues == []


def test_validate_duplicate_key():
    f = _file(_entry("A", "1", 1), _entry("A", "2", 2))
    result = validate_file(f)
    assert not result.ok
    assert len(result.errors) == 1
    assert "duplicate" in result.errors[0].message


def test_validate_empty_value_warning():
    f = _file(_entry("A", "", 1))
    result = validate_file(f)
    assert result.ok  # warning, not error
    assert len(result.warnings) == 1
    assert "empty" in result.warnings[0].message


def test_validate_key_with_space():
    entry = EnvEntry(
        key="MY KEY",
        value="v",
        raw="MY KEY=v",
        comment=False,
        blank=False,
        line_number=1,
    )
    f = _file(entry)
    result = validate_file(f)
    assert not result.ok
    assert any("whitespace" in i.message for i in result.errors)


def test_validate_comments_and_blanks_skipped():
    blank = EnvEntry(key=None, value=None, raw="", comment=False, blank=True, line_number=1)
    comment = EnvEntry(key=None, value=None, raw="# hi", comment=True, blank=False, line_number=2)
    f = _file(blank, comment)
    result = validate_file(f)
    assert result.ok
    assert result.issues == []

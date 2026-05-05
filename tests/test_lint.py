"""Tests for envpatch.lint."""
from __future__ import annotations

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.lint import LintSeverity, LintIssue, LintResult, lint


def _entry(
    key: str,
    value: str = "val",
    raw_value: str | None = None,
    is_comment: bool = False,
    is_secret: bool = False,
) -> EnvEntry:
    return EnvEntry(
        key=key,
        value=value,
        raw_value=raw_value if raw_value is not None else value,
        is_comment=is_comment,
        is_secret=is_secret,
    )


def _file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


# ---------------------------------------------------------------------------
# LintResult helpers
# ---------------------------------------------------------------------------

def test_result_ok_when_no_issues():
    result = LintResult()
    assert result.ok is True


def test_result_not_ok_when_error_present():
    result = LintResult(issues=[LintIssue(1, "K", "bad", LintSeverity.ERROR)])
    assert result.ok is False


def test_result_ok_with_only_warnings():
    result = LintResult(issues=[LintIssue(1, "k", "warn", LintSeverity.WARNING)])
    assert result.ok is True


def test_issue_str_contains_severity_and_key():
    issue = LintIssue(3, "MY_KEY", "something wrong", LintSeverity.ERROR)
    s = str(issue)
    assert "ERROR" in s
    assert "MY_KEY" in s
    assert "3" in s


# ---------------------------------------------------------------------------
# Uppercase check
# ---------------------------------------------------------------------------

def test_lowercase_key_is_warning():
    result = lint(_file(_entry("my_key")))
    assert any("uppercase" in i.message for i in result.warnings)


def test_uppercase_key_no_warning():
    result = lint(_file(_entry("MY_KEY")))
    assert not any("uppercase" in i.message for i in result.issues)


# ---------------------------------------------------------------------------
# Key starts with digit
# ---------------------------------------------------------------------------

def test_key_starting_with_digit_is_error():
    result = lint(_file(_entry("1BAD")))
    assert any("digit" in i.message for i in result.errors)


# ---------------------------------------------------------------------------
# Key with spaces
# ---------------------------------------------------------------------------

def test_key_with_space_is_error():
    result = lint(_file(_entry("MY KEY")))
    assert any("spaces" in i.message for i in result.errors)


# ---------------------------------------------------------------------------
# Empty value
# ---------------------------------------------------------------------------

def test_empty_value_is_warning():
    result = lint(_file(_entry("MY_KEY", value="", raw_value="")))
    assert any("empty" in i.message for i in result.warnings)


# ---------------------------------------------------------------------------
# Duplicate keys
# ---------------------------------------------------------------------------

def test_duplicate_key_is_error():
    f = _file(_entry("MY_KEY"), _entry("MY_KEY", value="other"))
    result = lint(f)
    assert any("duplicate" in i.message for i in result.errors)


def test_no_duplicate_for_unique_keys():
    f = _file(_entry("KEY_A"), _entry("KEY_B"))
    result = lint(f)
    assert not any("duplicate" in i.message for i in result.issues)


# ---------------------------------------------------------------------------
# Comments are skipped
# ---------------------------------------------------------------------------

def test_comment_entries_skipped():
    f = _file(_entry("", value="", is_comment=True))
    result = lint(f)
    assert result.issues == []

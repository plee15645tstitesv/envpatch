"""Tests for envpatch.schema."""

from __future__ import annotations

from envpatch.parser import EnvEntry, EnvFile
from envpatch.schema import SchemaResult, SchemaViolation, check_schema


def _entry(key: str, value: str = "x", line_number: int = 1) -> EnvEntry:
    return EnvEntry(
        key=key,
        value=value,
        raw=f"{key}={value}",
        comment=False,
        blank=False,
        line_number=line_number,
    )


def _file(*keys: str) -> EnvFile:
    return EnvFile(
        entries=[_entry(k, line_number=i + 1) for i, k in enumerate(keys)],
        path=None,
    )


def test_schema_ok_exact_match():
    tmpl = _file("A", "B", "C")
    target = _file("A", "B", "C")
    result = check_schema(tmpl, target)
    assert result.ok
    assert result.missing == []
    assert result.extra == []


def test_schema_missing_key():
    tmpl = _file("A", "B", "C")
    target = _file("A", "B")
    result = check_schema(tmpl, target)
    assert not result.ok
    assert "C" in result.missing


def test_schema_extra_key_ignored_by_default():
    tmpl = _file("A")
    target = _file("A", "EXTRA")
    result = check_schema(tmpl, target)
    assert result.ok
    assert result.extra == []


def test_schema_extra_key_reported_when_disallowed():
    tmpl = _file("A")
    target = _file("A", "EXTRA")
    result = check_schema(tmpl, target, allow_extra=False)
    assert result.ok  # missing is empty, so still ok
    assert "EXTRA" in result.extra


def test_schema_violations_list():
    tmpl = _file("A", "B")
    target = _file("A")
    result = check_schema(tmpl, target)
    viols = result.violations
    assert len(viols) == 1
    assert isinstance(viols[0], SchemaViolation)
    assert viols[0].key == "B"


def test_schema_result_str_pass():
    r = SchemaResult()
    assert "passed" in str(r)


def test_schema_result_str_shows_missing():
    r = SchemaResult(missing=["SECRET_KEY"])
    text = str(r)
    assert "MISSING" in text
    assert "SECRET_KEY" in text


def test_schema_result_str_shows_extra():
    r = SchemaResult(extra=["DEBUG"])
    text = str(r)
    assert "EXTRA" in text
    assert "DEBUG" in text


def test_schema_empty_template_always_passes():
    tmpl = _file()
    target = _file("A", "B")
    result = check_schema(tmpl, target)
    assert result.ok

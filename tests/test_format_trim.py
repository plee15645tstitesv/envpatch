"""Tests for envpatch.format_trim."""
from __future__ import annotations

from envpatch.parser import EnvEntry, EnvFile
from envpatch.trim import TrimResult, trim
from envpatch.format_trim import format_trim_summary, format_trim_detail, format_trim_output


def _result(
    empty: list[str] | None = None,
    duplicate: list[str] | None = None,
    unused: list[str] | None = None,
) -> TrimResult:
    r = TrimResult()
    r.removed_empty = empty or []
    r.removed_duplicate = duplicate or []
    r.removed_unused = unused or []
    return r


def test_summary_no_colour_contains_counts():
    r = _result(empty=["A"], duplicate=["B", "C"])
    text = format_trim_summary(r, colour=False)
    assert "3" in text
    assert "empty" in text
    assert "duplicate" in text


def test_summary_nothing_removed():
    r = _result()
    text = format_trim_summary(r, colour=False)
    assert "0" in text


def test_summary_with_colour_contains_ansi():
    r = _result(empty=["X"])
    text = format_trim_summary(r, colour=True)
    assert "\033[" in text


def test_detail_empty_section_present():
    r = _result(empty=["EMPTY_KEY"])
    text = format_trim_detail(r, colour=False)
    assert "Empty" in text
    assert "EMPTY_KEY" in text


def test_detail_duplicate_section_present():
    r = _result(duplicate=["DUP"])
    text = format_trim_detail(r, colour=False)
    assert "Duplicate" in text
    assert "DUP" in text


def test_detail_unused_section_present():
    r = _result(unused=["OLD"])
    text = format_trim_detail(r, colour=False)
    assert "Unused" in text
    assert "OLD" in text


def test_detail_nothing_trimmed_message():
    r = _result()
    text = format_trim_detail(r, colour=False)
    assert "Nothing trimmed" in text


def test_detail_with_colour_contains_ansi():
    r = _result(empty=["K"])
    text = format_trim_detail(r, colour=True)
    assert "\033[" in text


def test_output_returns_string():
    entry = EnvEntry(key="FOO", value="bar", raw="FOO=bar", is_comment=False, is_secret=False)
    r = TrimResult(entries=[entry])
    text = format_trim_output(r)
    assert isinstance(text, str)
    assert "FOO" in text

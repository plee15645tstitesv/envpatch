"""Tests for envpatch.format_sort."""
from __future__ import annotations

from envpatch.parser import EnvEntry, EnvFile
from envpatch.sort import SortResult, sort
from envpatch.format_sort import (
    format_sort_header,
    format_sort_summary,
    format_sort_output,
)


def _entry(key: str, value: str = "v") -> EnvEntry:
    return EnvEntry(key=key, value=value, comment=False, raw=f"{key}={value}")


def _result(**kwargs) -> SortResult:
    f = EnvFile(entries=[_entry("B"), _entry("A")])
    return sort(f, source_env=kwargs.get("source_env", "staging"))


def test_header_contains_source_env():
    r = _result(source_env="production")
    assert "production" in format_sort_header(r)


def test_header_no_colour_no_ansi():
    r = _result()
    header = format_sort_header(r, colour=False)
    assert "\033[" not in header


def test_header_with_colour_contains_ansi():
    r = _result()
    header = format_sort_header(r, colour=True)
    assert "\033[" in header


def test_summary_contains_sorted_count():
    r = _result()
    summary = format_sort_summary(r)
    assert str(r.total_sorted) in summary


def test_summary_contains_comment_count():
    r = _result()
    summary = format_sort_summary(r)
    assert str(r.total_comments) in summary


def test_summary_with_colour_contains_ansi():
    r = _result()
    summary = format_sort_summary(r, colour=True)
    assert "\033[" in summary


def test_output_contains_header_and_summary():
    r = _result(source_env="dev")
    output = format_sort_output(r)
    assert "dev" in output
    assert str(r.total_sorted) in output


def test_output_contains_sorted_keys():
    r = _result()
    output = format_sort_output(r)
    assert "A" in output
    assert "B" in output

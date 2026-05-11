"""Tests for envpatch.dedupe and envpatch.format_dedupe."""
from __future__ import annotations

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.dedupe import dedupe, DedupeResult
from envpatch.format_dedupe import (
    format_dedupe_summary,
    format_dedupe_detail,
    format_dedupe_report,
)


def _entry(key: str, value: str = "val", *, secret: bool = False) -> EnvEntry:
    return EnvEntry(key=key, value=value, is_comment=False, raw=f"{key}={value}", secret=secret)


def _comment(text: str = "# comment") -> EnvEntry:
    return EnvEntry(key=None, value=None, is_comment=True, raw=text, secret=False)


def _file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


# ---------------------------------------------------------------------------
# dedupe logic
# ---------------------------------------------------------------------------

def test_dedupe_no_duplicates_is_ok():
    f = _file(_entry("A"), _entry("B"))
    result = dedupe(f)
    assert result.ok()
    assert result.total_removed == 0
    assert result.duplicate_keys == []


def test_dedupe_keeps_last_by_default():
    first = _entry("KEY", "first")
    second = _entry("KEY", "second")
    result = dedupe(_file(first, second))
    assert not result.ok()
    kept = [e for e in result.deduplicated.entries if not e.is_comment]
    assert len(kept) == 1
    assert kept[0].value == "second"


def test_dedupe_keep_first():
    first = _entry("KEY", "first")
    second = _entry("KEY", "second")
    result = dedupe(_file(first, second), keep="first")
    kept = [e for e in result.deduplicated.entries if not e.is_comment]
    assert kept[0].value == "first"


def test_dedupe_total_removed_counts_extras():
    entries = [_entry("K", str(i)) for i in range(4)]
    result = dedupe(_file(*entries))
    assert result.total_removed == 3


def test_dedupe_preserves_comments_and_unique_keys():
    f = _file(_comment(), _entry("A"), _entry("B"), _entry("A", "dup"))
    result = dedupe(f)
    keys = [e.key for e in result.deduplicated.entries if not e.is_comment]
    assert keys == ["B", "A"]
    assert any(e.is_comment for e in result.deduplicated.entries)


def test_dedupe_invalid_keep_raises():
    with pytest.raises(ValueError, match="keep must be"):
        dedupe(_file(_entry("A")), keep="middle")


def test_dedupe_multiple_duplicate_keys():
    f = _file(_entry("X"), _entry("Y"), _entry("X", "x2"), _entry("Y", "y2"))
    result = dedupe(f)
    assert sorted(result.duplicate_keys) == ["X", "Y"]
    assert result.total_removed == 2


# ---------------------------------------------------------------------------
# format helpers
# ---------------------------------------------------------------------------

def _result_ok() -> DedupeResult:
    f = _file(_entry("A"), _entry("B"))
    return dedupe(f)


def _result_dup() -> DedupeResult:
    f = _file(_entry("KEY", "v1"), _entry("OTHER"), _entry("KEY", "v2"))
    return dedupe(f)


def test_summary_ok_no_colour():
    summary = format_dedupe_summary(_result_ok(), colour=False)
    assert "No duplicate" in summary


def test_summary_dup_no_colour():
    summary = format_dedupe_summary(_result_dup(), colour=False)
    assert "1 duplicate" in summary
    assert "removed 1" in summary


def test_summary_with_colour_contains_ansi():
    summary = format_dedupe_summary(_result_dup(), colour=True)
    assert "\033[" in summary


def test_detail_empty_when_ok():
    assert format_dedupe_detail(_result_ok()) == ""


def test_detail_lists_key():
    detail = format_dedupe_detail(_result_dup(), colour=False)
    assert "KEY" in detail
    assert "2" in detail


def test_report_ok_no_detail():
    report = format_dedupe_report(_result_ok(), colour=False)
    assert "\n" not in report


def test_report_dup_includes_detail():
    report = format_dedupe_report(_result_dup(), colour=False)
    assert "KEY" in report
    assert "duplicate" in report

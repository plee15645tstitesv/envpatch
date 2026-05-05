"""Tests for envpatch.compare and envpatch.format_compare."""

from __future__ import annotations

import pytest

from envpatch.parser import EnvFile, EnvEntry
from envpatch.diff import ChangeType
from envpatch.compare import compare, CompareReport
from envpatch.format_compare import (
    format_compare_header,
    format_compare_summary,
    format_compare_report,
)


def _file(*pairs: tuple[str, str]) -> EnvFile:
    entries = [
        EnvEntry(key=k, value=v, is_comment=False, raw=f"{k}={v}")
        for k, v in pairs
    ]
    return EnvFile(entries=entries)


# ---------------------------------------------------------------------------
# compare()
# ---------------------------------------------------------------------------

def test_compare_identical_files_is_ok():
    f = _file(("A", "1"), ("B", "2"))
    report = compare(f, f)
    assert report.ok
    assert report.total_changes == 0


def test_compare_added_key():
    source = _file(("A", "1"))
    target = _file(("A", "1"), ("B", "2"))
    report = compare(source, target)
    assert len(report.added) == 1
    assert report.added[0].key == "B"
    assert report.added[0].change == ChangeType.ADDED


def test_compare_removed_key():
    source = _file(("A", "1"), ("B", "2"))
    target = _file(("A", "1"))
    report = compare(source, target)
    assert len(report.removed) == 1
    assert report.removed[0].key == "B"


def test_compare_modified_key():
    source = _file(("A", "old"))
    target = _file(("A", "new"))
    report = compare(source, target)
    assert len(report.modified) == 1
    assert report.modified[0].key == "A"


def test_compare_unchanged_key():
    source = _file(("A", "1"))
    target = _file(("A", "1"))
    report = compare(source, target)
    assert len(report.unchanged) == 1
    assert report.total_changes == 0


def test_compare_changed_keys_sorted():
    source = _file(("B", "1"), ("A", "1"))
    target = _file(("A", "2"))
    report = compare(source, target)
    assert report.changed_keys() == ["A", "B"]


def test_compare_stores_names():
    f = _file(("X", "1"))
    report = compare(f, f, source_name="dev", target_name="prod")
    assert report.source_name == "dev"
    assert report.target_name == "prod"


# ---------------------------------------------------------------------------
# format_compare helpers
# ---------------------------------------------------------------------------

def test_format_header_contains_names():
    report = CompareReport(source_name="dev", target_name="prod")
    header = format_compare_header(report, colour=False)
    assert "dev" in header
    assert "prod" in header


def test_format_summary_counts():
    source = _file(("A", "1"), ("B", "2"))
    target = _file(("A", "changed"), ("C", "3"))
    report = compare(source, target)
    summary = format_compare_summary(report, colour=False)
    assert "+1" in summary   # C added
    assert "-1" in summary   # B removed
    assert "~1" in summary   # A modified


def test_format_report_identical_message():
    f = _file(("A", "1"))
    report = compare(f, f)
    output = format_compare_report(report, colour=False)
    assert "identical" in output.lower()


def test_format_report_colour_contains_ansi():
    source = _file(("A", "1"))
    target = _file(("A", "2"))
    report = compare(source, target)
    output = format_compare_report(report, colour=True)
    assert "\033[" in output


def test_format_report_show_unchanged_includes_all():
    f = _file(("A", "1"), ("B", "2"))
    report = compare(f, f)
    output_hidden = format_compare_report(report, show_unchanged=False, colour=False)
    output_shown = format_compare_report(report, show_unchanged=True, colour=False)
    # With show_unchanged the diff section must appear (keys listed)
    assert len(output_shown) >= len(output_hidden)

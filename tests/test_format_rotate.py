"""Tests for envpatch.format_rotate."""
from __future__ import annotations

from envpatch.format_rotate import (
    format_rotate_detail,
    format_rotate_not_ok,
    format_rotate_summary,
)
from envpatch.rotate import RotateResult


def _result(
    rotated: list[str] | None = None,
    skipped: list[str] | None = None,
    errors: list[str] | None = None,
) -> RotateResult:
    return RotateResult(
        rotated=rotated or [],
        skipped=skipped or [],
        errors=errors or [],
    )


def test_summary_no_colour_contains_counts():
    r = _result(rotated=["A", "B"], skipped=["C"], errors=[])
    out = format_rotate_summary(r, colour=False)
    assert "2 rotated" in out
    assert "1 skipped" in out
    assert "0 errors" in out


def test_summary_with_colour_contains_ansi():
    r = _result(rotated=["A"])
    out = format_rotate_summary(r, colour=True)
    assert "\033[" in out


def test_detail_lists_rotated_keys():
    r = _result(rotated=["TOKEN", "SECRET"])
    out = format_rotate_detail(r, colour=False)
    assert "TOKEN" in out
    assert "SECRET" in out


def test_detail_lists_skipped_keys():
    r = _result(skipped=["HOST"])
    out = format_rotate_detail(r, colour=False)
    assert "HOST" in out
    assert "skipped" in out


def test_detail_lists_error_keys():
    r = _result(errors=["BAD"])
    out = format_rotate_detail(r, colour=False)
    assert "BAD" in out
    assert "error" in out


def test_detail_empty_shows_placeholder():
    r = _result()
    out = format_rotate_detail(r, colour=False)
    assert "no entries" in out


def test_not_ok_mentions_failed_keys():
    r = _result(errors=["KEY1", "KEY2"])
    out = format_rotate_not_ok(r, colour=False)
    assert "KEY1" in out
    assert "KEY2" in out


def test_not_ok_with_colour_contains_ansi():
    r = _result(errors=["X"])
    out = format_rotate_not_ok(r, colour=True)
    assert "\033[" in out

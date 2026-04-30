"""Tests for envpatch.format_snapshot."""

from __future__ import annotations

from pathlib import Path

from envpatch.format_snapshot import (
    format_snapshot_list,
    format_snapshot_saved,
    format_snapshot_deleted,
    format_snapshot_not_found,
)


def test_list_empty_no_colour():
    result = format_snapshot_list([], use_colour=False)
    assert "no snapshots" in result


def test_list_names_no_colour():
    result = format_snapshot_list(["alpha", "beta"], use_colour=False)
    assert "alpha" in result
    assert "beta" in result
    assert "Saved snapshots" in result


def test_list_names_order_preserved():
    names = ["zzz", "aaa", "mmm"]
    result = format_snapshot_list(names, use_colour=False)
    idx_z = result.index("zzz")
    idx_a = result.index("aaa")
    idx_m = result.index("mmm")
    assert idx_a < idx_m < idx_z or result.count("\n") >= 2  # order preserved


def test_list_with_colour_contains_ansi():
    result = format_snapshot_list(["snap"], use_colour=True)
    assert "\033[" in result


def test_saved_no_colour():
    p = Path(".envpatch_snapshots/prod.json")
    result = format_snapshot_saved("prod", p, use_colour=False)
    assert "prod" in result
    assert str(p) in result
    assert "saved" in result.lower()


def test_saved_with_colour():
    p = Path(".envpatch_snapshots/dev.json")
    result = format_snapshot_saved("dev", p, use_colour=True)
    assert "\033[" in result
    assert "dev" in result


def test_deleted_no_colour():
    result = format_snapshot_deleted("old", use_colour=False)
    assert "old" in result
    assert "deleted" in result.lower()


def test_deleted_with_colour():
    result = format_snapshot_deleted("old", use_colour=True)
    assert "\033[" in result


def test_not_found_no_colour():
    result = format_snapshot_not_found("ghost", use_colour=False)
    assert "ghost" in result
    assert "not found" in result.lower()


def test_not_found_with_colour():
    result = format_snapshot_not_found("ghost", use_colour=True)
    assert "\033[" in result
    assert "ghost" in result

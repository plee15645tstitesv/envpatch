"""Tests for envpatch.format_tag."""
from __future__ import annotations

from envpatch.tag import TagEntry, TagResult
from envpatch.format_tag import format_tag_summary, format_tag_detail, format_tag_filter


def _result(
    tagged: list[tuple[str, list[str]]] | None = None,
    untagged: list[str] | None = None,
) -> TagResult:
    r = TagResult(
        tagged=[TagEntry(key=k, tags=t) for k, t in (tagged or [])],
        untagged_keys=list(untagged or []),
    )
    return r


# ---------------------------------------------------------------------------
# format_tag_summary
# ---------------------------------------------------------------------------

def test_summary_no_colour_contains_counts():
    r = _result(tagged=[("A", ["x"]), ("B", ["y"])], untagged=["C"])
    out = format_tag_summary(r, colour=False)
    assert "2" in out
    assert "1" in out


def test_summary_with_colour_contains_ansi():
    r = _result(tagged=[("A", ["x"])], untagged=[])
    out = format_tag_summary(r, colour=True)
    assert "\033[" in out


def test_summary_zero_counts():
    r = _result()
    out = format_tag_summary(r, colour=False)
    assert "tagged: 0" in out
    assert "untagged: 0" in out


# ---------------------------------------------------------------------------
# format_tag_detail
# ---------------------------------------------------------------------------

def test_detail_lists_tagged_keys():
    r = _result(tagged=[("DB_HOST", ["database"]), ("APP_KEY", ["auth"])])
    out = format_tag_detail(r, colour=False)
    assert "DB_HOST" in out
    assert "APP_KEY" in out
    assert "database" in out
    assert "auth" in out


def test_detail_lists_untagged_section():
    r = _result(tagged=[("A", ["x"])], untagged=["B", "C"])
    out = format_tag_detail(r, colour=False)
    assert "untagged" in out
    assert "B" in out
    assert "C" in out


def test_detail_no_untagged_section_when_empty():
    r = _result(tagged=[("A", ["x"])], untagged=[])
    out = format_tag_detail(r, colour=False)
    assert "untagged" not in out


def test_detail_with_colour_contains_ansi():
    r = _result(tagged=[("X", ["t"])], untagged=["Y"])
    out = format_tag_detail(r, colour=True)
    assert "\033[" in out


# ---------------------------------------------------------------------------
# format_tag_filter
# ---------------------------------------------------------------------------

def test_filter_header_contains_tag_name():
    out = format_tag_filter("database", ["DB_HOST"], colour=False)
    assert "database" in out


def test_filter_lists_keys():
    out = format_tag_filter("db", ["DB_HOST", "DB_PORT"], colour=False)
    assert "DB_HOST" in out
    assert "DB_PORT" in out


def test_filter_empty_keys_shows_none():
    out = format_tag_filter("missing", [], colour=False)
    assert "(none)" in out


def test_filter_with_colour_contains_ansi():
    out = format_tag_filter("x", ["K"], colour=True)
    assert "\033[" in out

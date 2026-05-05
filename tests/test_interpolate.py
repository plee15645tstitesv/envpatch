"""Tests for envpatch.interpolate."""

from __future__ import annotations

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.interpolate import interpolate, InterpolationError


def _file(*pairs: tuple[str, str]) -> EnvFile:
    entries = [
        EnvEntry(key=k, value=v, is_comment=False, raw=f"{k}={v}")
        for k, v in pairs
    ]
    return EnvFile(entries=entries)


def _comment(text: str) -> EnvEntry:
    return EnvEntry(key=None, value=None, is_comment=True, raw=text)


# ---------------------------------------------------------------------------
# Basic resolution
# ---------------------------------------------------------------------------

def test_brace_syntax_resolved():
    f = _file(("HOME", "/home/user"), ("CONFIG", "${HOME}/.config"))
    result = interpolate(f)
    vals = {e.key: e.value for e in result.entries if e.key}
    assert vals["CONFIG"] == "/home/user/.config"


def test_bare_dollar_syntax_resolved():
    f = _file(("DIR", "/opt"), ("BIN", "$DIR/bin"))
    result = interpolate(f)
    vals = {e.key: e.value for e in result.entries if e.key}
    assert vals["BIN"] == "/opt/bin"


def test_no_interpolation_needed():
    f = _file(("FOO", "bar"), ("BAZ", "qux"))
    result = interpolate(f)
    vals = {e.key: e.value for e in result.entries if e.key}
    assert vals == {"FOO": "bar", "BAZ": "qux"}


def test_multiple_refs_in_one_value():
    f = _file(("A", "hello"), ("B", "world"), ("C", "${A} ${B}"))
    result = interpolate(f)
    vals = {e.key: e.value for e in result.entries if e.key}
    assert vals["C"] == "hello world"


# ---------------------------------------------------------------------------
# Extra context
# ---------------------------------------------------------------------------

def test_extra_context_used():
    f = _file(("PATH", "${BASE}/bin"))
    result = interpolate(f, extra={"BASE": "/usr"})
    vals = {e.key: e.value for e in result.entries if e.key}
    assert vals["PATH"] == "/usr/bin"


def test_file_value_overrides_extra():
    """A key defined earlier in the file takes precedence over extra."""
    f = _file(("BASE", "/home"), ("PATH", "${BASE}/bin"))
    result = interpolate(f, extra={"BASE": "/usr"})
    vals = {e.key: e.value for e in result.entries if e.key}
    # BASE is set in file first, so PATH should use /home
    assert vals["PATH"] == "/home/bin"


# ---------------------------------------------------------------------------
# Strict mode
# ---------------------------------------------------------------------------

def test_strict_raises_on_unresolved():
    f = _file(("X", "${UNDEFINED}"))
    with pytest.raises(InterpolationError) as exc_info:
        interpolate(f, strict=True)
    assert exc_info.value.ref == "UNDEFINED"
    assert "X" in str(exc_info.value)


def test_non_strict_leaves_placeholder():
    f = _file(("X", "${UNDEFINED}"))
    result = interpolate(f, strict=False)
    vals = {e.key: e.value for e in result.entries if e.key}
    assert vals["X"] == "${UNDEFINED}"


# ---------------------------------------------------------------------------
# Comments and blank entries are preserved unchanged
# ---------------------------------------------------------------------------

def test_comments_preserved():
    comment = _comment("# this is a comment")
    f = EnvFile(entries=[comment, *_file(("A", "1")).entries])
    result = interpolate(f)
    assert result.entries[0].is_comment
    assert result.entries[0].raw == "# this is a comment"

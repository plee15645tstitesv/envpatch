"""Tests for envpatch.rename."""
from __future__ import annotations

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.rename import rename


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _entry(key: str, value: str = "val") -> EnvEntry:
    return EnvEntry(key=key, value=value, is_comment=False, raw=f"{key}={value}")


def _comment(text: str = "# note") -> EnvEntry:
    return EnvEntry(key=None, value=None, is_comment=True, raw=text)


def _file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


# ---------------------------------------------------------------------------
# RenameResult helpers
# ---------------------------------------------------------------------------

def test_rename_returns_result():
    result = rename(_file(_entry("A")), {"A": "B"})
    assert result is not None


def test_rename_ok_when_all_keys_found():
    result = rename(_file(_entry("A")), {"A": "B"})
    assert result.ok() is True


def test_rename_not_ok_when_key_missing():
    result = rename(_file(_entry("A")), {"MISSING": "B"})
    assert result.ok() is False


def test_rename_total_renamed_count():
    result = rename(_file(_entry("A"), _entry("C")), {"A": "B", "C": "D"})
    assert result.total_renamed() == 2


def test_rename_total_not_found_count():
    result = rename(_file(_entry("A")), {"A": "B", "NOPE": "X"})
    assert result.total_not_found() == 1


# ---------------------------------------------------------------------------
# Key renaming behaviour
# ---------------------------------------------------------------------------

def test_rename_key_appears_in_output():
    result = rename(_file(_entry("OLD", "secret")), {"OLD": "NEW"})
    keys = [e.key for e in result.entries if not e.is_comment]
    assert "NEW" in keys
    assert "OLD" not in keys


def test_rename_value_preserved():
    result = rename(_file(_entry("OLD", "myvalue")), {"OLD": "NEW"})
    entry = next(e for e in result.entries if e.key == "NEW")
    assert entry.value == "myvalue"


def test_rename_untouched_keys_unchanged():
    result = rename(_file(_entry("A", "1"), _entry("B", "2")), {"A": "Z"})
    keys = [e.key for e in result.entries if not e.is_comment]
    assert "B" in keys
    assert "Z" in keys


def test_rename_comments_pass_through():
    result = rename(_file(_comment("# header"), _entry("A")), {"A": "B"})
    comments = [e for e in result.entries if e.is_comment]
    assert len(comments) == 1
    assert comments[0].raw == "# header"


def test_rename_multiple_keys():
    result = rename(
        _file(_entry("X"), _entry("Y"), _entry("Z")),
        {"X": "A", "Z": "C"},
    )
    keys = [e.key for e in result.entries if not e.is_comment]
    assert keys == ["A", "Y", "C"]


# ---------------------------------------------------------------------------
# Missing-key behaviour
# ---------------------------------------------------------------------------

def test_rename_missing_key_recorded_in_not_found():
    result = rename(_file(_entry("A")), {"GHOST": "B"})
    assert "GHOST" in result.not_found


def test_rename_error_on_missing_raises():
    with pytest.raises(KeyError, match="GHOST"):
        rename(_file(_entry("A")), {"GHOST": "B"}, error_on_missing=True)


def test_rename_as_env_file_type():
    result = rename(_file(_entry("A")), {"A": "B"})
    env = result.as_env_file()
    assert hasattr(env, "entries")


def test_rename_renamed_dict_maps_old_to_new():
    result = rename(_file(_entry("FOO")), {"FOO": "BAR"})
    assert result.renamed == {"FOO": "BAR"}

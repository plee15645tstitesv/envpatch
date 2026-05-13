"""Tests for envpatch.group."""
from __future__ import annotations

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.group import GroupResult, group


def _entry(key: str, value: str = "val", secret: bool = False) -> EnvEntry:
    return EnvEntry(key=key, value=value, secret=secret, comment=False, raw=f"{key}={value}")


def _comment(text: str = "# section") -> EnvEntry:
    return EnvEntry(key="", value="", secret=False, comment=True, raw=text)


def _file(*entries: EnvEntry, env: str = "test") -> EnvFile:
    return EnvFile(env=env, entries=list(entries))


# ---------------------------------------------------------------------------
# Basic grouping
# ---------------------------------------------------------------------------

def test_group_returns_result():
    f = _file(_entry("DB_HOST"), _entry("DB_PORT"))
    result = group(f)
    assert isinstance(result, GroupResult)


def test_group_ok_always_true():
    result = group(_file(_entry("A_B")))
    assert result.ok() is True


def test_group_single_prefix():
    f = _file(_entry("DB_HOST"), _entry("DB_PORT"), _entry("DB_NAME"))
    result = group(f)
    assert "DB" in result.groups
    assert len(result.groups["DB"]) == 3


def test_group_multiple_prefixes():
    f = _file(_entry("DB_HOST"), _entry("REDIS_URL"), _entry("DB_PORT"))
    result = group(f)
    assert set(result.groups.keys()) == {"DB", "REDIS"}
    assert len(result.groups["DB"]) == 2
    assert len(result.groups["REDIS"]) == 1


def test_group_no_separator_goes_to_ungrouped():
    f = _file(_entry("HOST"), _entry("PORT"))
    result = group(f)
    assert result.groups == {}
    assert len(result.ungrouped) == 2


def test_group_mixed_grouped_and_ungrouped():
    f = _file(_entry("DB_HOST"), _entry("PORT"))
    result = group(f)
    assert len(result.groups["DB"]) == 1
    assert len(result.ungrouped) == 1


def test_group_total_grouped():
    f = _file(_entry("DB_HOST"), _entry("DB_PORT"), _entry("REDIS_URL"))
    result = group(f)
    assert result.total_grouped() == 3


def test_group_total_ungrouped():
    f = _file(_entry("HOST"), _entry("PORT"))
    result = group(f)
    assert result.total_ungrouped() == 2


def test_group_names_sorted():
    f = _file(_entry("Z_KEY"), _entry("A_KEY"), _entry("M_KEY"))
    result = group(f)
    assert result.group_names() == ["A", "M", "Z"]


# ---------------------------------------------------------------------------
# Custom separator
# ---------------------------------------------------------------------------

def test_group_custom_separator():
    f = _file(_entry("DB.HOST"), _entry("DB.PORT"))
    result = group(f, prefix_sep=".")
    assert "DB" in result.groups
    assert len(result.groups["DB"]) == 2


def test_group_default_sep_does_not_split_on_dot():
    f = _file(_entry("DB.HOST"))
    result = group(f)
    assert result.ungrouped[0].key == "DB.HOST"


# ---------------------------------------------------------------------------
# as_env_file
# ---------------------------------------------------------------------------

def test_as_env_file_returns_correct_entries():
    f = _file(_entry("DB_HOST"), _entry("DB_PORT"), _entry("REDIS_URL"))
    result = group(f)
    ef = result.as_env_file("DB")
    assert ef is not None
    assert len(ef.entries) == 2
    assert all(e.key.startswith("DB_") for e in ef.entries)


def test_as_env_file_missing_group_returns_none():
    f = _file(_entry("DB_HOST"))
    result = group(f)
    assert result.as_env_file("MISSING") is None


# ---------------------------------------------------------------------------
# Comment handling
# ---------------------------------------------------------------------------

def test_comments_excluded_by_default():
    f = _file(_comment("# db section"), _entry("DB_HOST"))
    result = group(f)
    assert all(not e.comment for e in result.groups.get("DB", []))


def test_comments_included_when_flag_set():
    f = _file(_comment("# db section"), _entry("DB_HOST"))
    result = group(f, include_comments=True)
    entries = result.groups["DB"]
    assert entries[0].comment is True
    assert entries[1].key == "DB_HOST"

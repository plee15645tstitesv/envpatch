"""Tests for envpatch.sort."""
from __future__ import annotations

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.sort import SortResult, sort


def _entry(key: str, value: str = "val") -> EnvEntry:
    return EnvEntry(key=key, value=value, comment=False, raw=f"{key}={value}")


def _comment(text: str = "# comment") -> EnvEntry:
    return EnvEntry(key=None, value=None, comment=True, raw=text)


def _file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


def test_sort_returns_result():
    f = _file(_entry("ZEBRA"), _entry("APPLE"))
    result = sort(f, source_env="test")
    assert isinstance(result, SortResult)
    assert result.source_env == "test"


def test_sort_ok_is_always_true():
    result = sort(_file(_entry("A")), source_env="x")
    assert result.ok() is True


def test_sort_orders_keys_alphabetically():
    f = _file(_entry("ZEBRA"), _entry("MANGO"), _entry("APPLE"))
    result = sort(f, source_env="test")
    key_entries = [e for e in result.entries if not e.comment]
    assert [e.key for e in key_entries] == ["APPLE", "MANGO", "ZEBRA"]


def test_sort_reverse_orders_descending():
    f = _file(_entry("APPLE"), _entry("MANGO"), _entry("ZEBRA"))
    result = sort(f, source_env="test", reverse=True)
    key_entries = [e for e in result.entries if not e.comment]
    assert [e.key for e in key_entries] == ["ZEBRA", "MANGO", "APPLE"]


def test_sort_preserves_comments_by_default():
    f = _file(_comment("# header"), _entry("B"), _entry("A"))
    result = sort(f)
    assert any(e.comment for e in result.entries)
    assert result.total_comments == 1


def test_sort_strip_comments_removes_them():
    f = _file(_comment("# header"), _entry("B"), _entry("A"))
    result = sort(f, strip_comments=True)
    assert all(not e.comment for e in result.entries)
    assert result.total_comments == 1  # counted but not included


def test_sort_total_sorted_counts_key_entries():
    f = _file(_entry("C"), _entry("A"), _entry("B"), _comment())
    result = sort(f)
    assert result.total_sorted == 3


def test_sort_group_by_prefix_clusters_same_prefix():
    f = _file(
        _entry("DB_HOST"),
        _entry("APP_NAME"),
        _entry("DB_PORT"),
        _entry("APP_ENV"),
    )
    result = sort(f, group_by_prefix=True)
    keys = [e.key for e in result.entries if not e.comment]
    # APP group before DB group; within each group sorted
    assert keys.index("APP_ENV") < keys.index("APP_NAME")
    assert keys.index("DB_HOST") < keys.index("DB_PORT")
    app_pos = min(keys.index("APP_ENV"), keys.index("APP_NAME"))
    db_pos = min(keys.index("DB_HOST"), keys.index("DB_PORT"))
    assert app_pos < db_pos


def test_sort_as_env_file_returns_env_file():
    from envpatch.parser import EnvFile
    f = _file(_entry("B"), _entry("A"))
    result = sort(f)
    env = result.as_env_file()
    assert isinstance(env, EnvFile)
    assert len(env.entries) == len(result.entries)


def test_sort_empty_file_is_ok():
    result = sort(_file())
    assert result.ok()
    assert result.total_sorted == 0
    assert result.total_comments == 0

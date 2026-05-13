"""Tests for envpatch.split."""
from __future__ import annotations

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.split import SplitResult, split


def _entry(key: str, value: str = "val") -> EnvEntry:
    return EnvEntry(key=key, value=value, comment=False, raw=f"{key}={value}")


def _comment(text: str = "# section") -> EnvEntry:
    return EnvEntry(key="", value="", comment=True, raw=text)


def _file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


# ---------------------------------------------------------------------------
# Basic behaviour
# ---------------------------------------------------------------------------

def test_split_returns_result():
    f = _file(_entry("DB_HOST"), _entry("APP_PORT"))
    result = split(f, ["DB_", "APP_"])
    assert isinstance(result, SplitResult)


def test_split_ok_is_always_true():
    result = split(_file(), [])
    assert result.ok is True


def test_split_source_env_stored():
    result = split(_file(), [], source_env="production")
    assert result.source_env == "production"


def test_split_matching_keys_go_to_correct_bucket():
    f = _file(_entry("DB_HOST"), _entry("DB_PORT"), _entry("APP_PORT"))
    result = split(f, ["DB_", "APP_"])
    db_keys = [e.key for e in result.buckets["DB_"].entries]
    app_keys = [e.key for e in result.buckets["APP_"].entries]
    assert "DB_HOST" in db_keys
    assert "DB_PORT" in db_keys
    assert "APP_PORT" in app_keys


def test_split_unmatched_keys_go_to_unmatched():
    f = _file(_entry("SECRET_KEY"), _entry("DB_HOST"))
    result = split(f, ["DB_"])
    unmatched_keys = [e.key for e in result.unmatched.entries]
    assert "SECRET_KEY" in unmatched_keys
    assert "DB_HOST" not in unmatched_keys


def test_split_total_keys_count():
    f = _file(_entry("DB_HOST"), _entry("DB_PORT"), _entry("APP_PORT"))
    result = split(f, ["DB_", "APP_"])
    assert result.total_keys == 3


def test_split_total_unmatched_count():
    f = _file(_entry("DB_HOST"), _entry("OTHER"), _entry("EXTRA"))
    result = split(f, ["DB_"])
    assert result.total_unmatched == 2


def test_split_bucket_names_returns_prefix_list():
    result = split(_file(), ["DB_", "APP_", "CACHE_"])
    assert result.bucket_names() == ["DB_", "APP_", "CACHE_"]


# ---------------------------------------------------------------------------
# strip_prefix
# ---------------------------------------------------------------------------

def test_strip_prefix_removes_prefix_from_key():
    f = _file(_entry("DB_HOST", "localhost"))
    result = split(f, ["DB_"], strip_prefix=True)
    keys = [e.key for e in result.buckets["DB_"].entries]
    assert "HOST" in keys
    assert "DB_HOST" not in keys


def test_strip_prefix_false_keeps_full_key():
    f = _file(_entry("DB_HOST", "localhost"))
    result = split(f, ["DB_"], strip_prefix=False)
    keys = [e.key for e in result.buckets["DB_"].entries]
    assert "DB_HOST" in keys


# ---------------------------------------------------------------------------
# include_comments
# ---------------------------------------------------------------------------

def test_include_comments_adds_comments_to_non_empty_buckets():
    f = _file(_comment("# db section"), _entry("DB_HOST"))
    result = split(f, ["DB_"], include_comments=True)
    raw_lines = [e.raw for e in result.buckets["DB_"].entries]
    assert "# db section" in raw_lines


def test_include_comments_false_omits_comments_from_buckets():
    f = _file(_comment("# header"), _entry("DB_HOST"))
    result = split(f, ["DB_"], include_comments=False)
    comments_in_bucket = [e for e in result.buckets["DB_"].entries if e.comment]
    assert comments_in_bucket == []


def test_comments_not_counted_in_total_keys():
    f = _file(_comment(), _entry("DB_HOST"), _entry("DB_PORT"))
    result = split(f, ["DB_"])
    assert result.total_keys == 2


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_empty_source_produces_empty_buckets():
    result = split(_file(), ["DB_", "APP_"])
    assert all(len(b.entries) == 0 for b in result.buckets.values())
    assert result.total_keys == 0


def test_first_matching_prefix_wins():
    """A key matching two prefixes should land in the first one only."""
    f = _file(_entry("DB_APP_HOST"))
    result = split(f, ["DB_", "DB_APP_"])
    assert len(result.buckets["DB_"].entries) == 1
    assert len(result.buckets["DB_APP_"].entries) == 0

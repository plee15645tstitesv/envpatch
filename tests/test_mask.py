"""Tests for envpatch.mask."""
from __future__ import annotations

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.mask import MaskResult, _mask_value, mask


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _entry(key: str, value: str, *, comment: bool = False) -> EnvEntry:
    raw = f"# {key}" if comment else f"{key}={value}"
    return EnvEntry(key=None if comment else key, value=None if comment else value, comment=comment, raw=raw)


def _file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


# ---------------------------------------------------------------------------
# _mask_value unit tests
# ---------------------------------------------------------------------------

def test_mask_value_hides_most_chars():
    result = _mask_value("supersecret", visible_chars=4, mask_char="*")
    assert result.endswith("cret")
    assert "*" in result


def test_mask_value_zero_visible_all_stars():
    result = _mask_value("abc", visible_chars=0, mask_char="*")
    assert set(result) == {"*"}


def test_mask_value_empty_string_unchanged():
    assert _mask_value("", visible_chars=4, mask_char="*") == ""


def test_mask_value_short_value_all_masked():
    # value shorter than visible_chars → fully masked
    result = _mask_value("ab", visible_chars=4, mask_char="*")
    assert "a" not in result and "b" not in result


# ---------------------------------------------------------------------------
# mask() integration tests
# ---------------------------------------------------------------------------

def test_mask_secret_key_is_masked():
    f = _file(_entry("SECRET_TOKEN", "abc123xyz"))
    result = mask(f)
    assert result.total_masked == 1
    entry = result.entries[0]
    assert "*" in (entry.value or "")
    assert (entry.value or "").endswith("xyz")


def test_mask_non_secret_key_not_masked_by_default():
    f = _file(_entry("APP_NAME", "myapp"))
    result = mask(f)
    assert result.total_masked == 0
    assert result.entries[0].value == "myapp"


def test_mask_explicit_keys_override_secrets_only():
    f = _file(_entry("APP_NAME", "myapp1234"))
    result = mask(f, keys=["APP_NAME"], secrets_only=False)
    assert result.total_masked == 1
    assert "*" in (result.entries[0].value or "")


def test_mask_secrets_only_false_explicit_keys_required():
    # secrets_only=False but no explicit keys → nothing masked
    f = _file(_entry("SECRET_KEY", "topsecret"))
    result = mask(f, keys=[], secrets_only=False)
    assert result.total_masked == 0


def test_mask_comment_entries_pass_through():
    f = _file(_entry("# just a comment", "", comment=True))
    result = mask(f)
    assert result.entries[0].comment is True
    assert result.total_masked == 0


def test_mask_result_ok_always_true():
    f = _file(_entry("DB_PASSWORD", "hunter2"))
    result = mask(f)
    assert result.ok() is True


def test_mask_as_env_file_returns_env_file():
    f = _file(_entry("API_SECRET", "hello"))
    result = mask(f)
    env = result.as_env_file()
    assert len(env.entries) == 1


def test_mask_visible_chars_customisable():
    f = _file(_entry("DB_PASSWORD", "abcdefgh"))
    result = mask(f, visible_chars=2)
    tail = (result.entries[0].value or "")[-2:]
    assert tail == "gh"


def test_mask_multiple_entries_counts_correctly():
    f = _file(
        _entry("SECRET_A", "value1"),
        _entry("APP_MODE", "production"),
        _entry("API_KEY", "key9999"),
    )
    result = mask(f)
    assert result.total_masked == 2  # SECRET_A and API_KEY
    assert result.total_visible == 1  # APP_MODE

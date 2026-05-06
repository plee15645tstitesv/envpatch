"""Tests for envpatch.rotate."""
from __future__ import annotations

import pytest

from envpatch.encrypt import encrypt_value, generate_key, is_encrypted
from envpatch.parser import EnvEntry, EnvFile
from envpatch.rotate import RotateResult, rotate


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _entry(key: str, value: str, *, comment: bool = False) -> EnvEntry:
    raw = f"# {value}" if comment else f"{key}={value}"
    return EnvEntry(key=None if comment else key, value=value,
                    is_comment=comment, raw=raw)


def _file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

def test_rotate_returns_result():
    old_key = generate_key()
    new_key = generate_key()
    enc = encrypt_value("secret", old_key)
    ef = _file(_entry("TOKEN", enc))
    result = rotate(ef, old_key, new_key)
    assert isinstance(result, RotateResult)


def test_rotate_encrypted_value_changes_ciphertext():
    old_key = generate_key()
    new_key = generate_key()
    enc = encrypt_value("secret", old_key)
    ef = _file(_entry("TOKEN", enc))
    result = rotate(ef, old_key, new_key)
    assert result.ok
    assert "TOKEN" in result.rotated
    new_val = result.file.entries[0].value
    assert new_val != enc
    assert is_encrypted(new_val)


def test_rotate_plaintext_value_is_skipped():
    old_key = generate_key()
    new_key = generate_key()
    ef = _file(_entry("HOST", "localhost"))
    result = rotate(ef, old_key, new_key)
    assert result.ok
    assert "HOST" in result.skipped
    assert result.total_rotated == 0


def test_rotate_comment_entry_passed_through():
    old_key = generate_key()
    new_key = generate_key()
    comment = _entry("", "a comment", comment=True)
    ef = _file(comment)
    result = rotate(ef, old_key, new_key)
    assert result.ok
    assert result.file.entries[0].is_comment


def test_rotate_wrong_old_key_records_error():
    old_key = generate_key()
    wrong_key = generate_key()
    new_key = generate_key()
    enc = encrypt_value("secret", old_key)
    ef = _file(_entry("TOKEN", enc))
    result = rotate(ef, wrong_key, new_key)
    assert not result.ok
    assert "TOKEN" in result.errors


def test_rotate_preserves_original_value_on_error():
    old_key = generate_key()
    wrong_key = generate_key()
    new_key = generate_key()
    enc = encrypt_value("secret", old_key)
    ef = _file(_entry("TOKEN", enc))
    result = rotate(ef, wrong_key, new_key)
    assert result.file.entries[0].value == enc


def test_rotate_multiple_keys_mixed():
    old_key = generate_key()
    new_key = generate_key()
    enc1 = encrypt_value("val1", old_key)
    enc2 = encrypt_value("val2", old_key)
    ef = _file(
        _entry("A", enc1),
        _entry("B", "plain"),
        _entry("C", enc2),
    )
    result = rotate(ef, old_key, new_key)
    assert result.ok
    assert result.total_rotated == 2
    assert result.total_skipped == 1

"""Tests for envpatch.sign and envpatch.format_sign."""
from __future__ import annotations

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.sign import (
    SignatureManifest,
    VerifyResult,
    sign_file,
    verify_file,
)
from envpatch.format_sign import format_sign_saved, format_verify_result

SECRET = "supersecret"


def _entry(key: str, value: str, *, is_comment: bool = False) -> EnvEntry:
    return EnvEntry(key=key, value=value, raw=f"{key}={value}", is_comment=is_comment)


def _file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


# ---------------------------------------------------------------------------
# sign_file
# ---------------------------------------------------------------------------

def test_sign_produces_entry_per_key():
    f = _file(_entry("A", "1"), _entry("B", "2"))
    manifest = sign_file(f, SECRET)
    keys = [e.key for e in manifest.entries]
    assert "A" in keys and "B" in keys


def test_sign_skips_comments():
    comment = EnvEntry(key=None, value=None, raw="# comment", is_comment=True)
    f = _file(comment, _entry("X", "val"))
    manifest = sign_file(f, SECRET)
    assert len(manifest.entries) == 1
    assert manifest.entries[0].key == "X"


def test_sign_file_digest_is_non_empty():
    f = _file(_entry("K", "v"))
    manifest = sign_file(f, SECRET)
    assert len(manifest.file_digest) == 64  # sha256 hex


def test_different_secrets_produce_different_digests():
    f = _file(_entry("K", "v"))
    m1 = sign_file(f, "secret1")
    m2 = sign_file(f, "secret2")
    assert m1.file_digest != m2.file_digest


# ---------------------------------------------------------------------------
# verify_file
# ---------------------------------------------------------------------------

def test_verify_valid_file_is_ok():
    f = _file(_entry("A", "hello"), _entry("B", "world"))
    manifest = sign_file(f, SECRET)
    result = verify_file(f, manifest, SECRET)
    assert result.ok
    assert result.tampered_keys == []
    assert result.missing_keys == []
    assert result.file_digest_ok


def test_verify_detects_tampered_value():
    f = _file(_entry("A", "hello"))
    manifest = sign_file(f, SECRET)
    tampered = _file(_entry("A", "HACKED"))
    result = verify_file(tampered, manifest, SECRET)
    assert not result.ok
    assert "A" in result.tampered_keys


def test_verify_detects_removed_key():
    f = _file(_entry("A", "1"), _entry("B", "2"))
    manifest = sign_file(f, SECRET)
    reduced = _file(_entry("A", "1"))
    result = verify_file(reduced, manifest, SECRET)
    assert not result.ok
    assert "B" in result.missing_keys


def test_verify_wrong_secret_fails():
    f = _file(_entry("K", "v"))
    manifest = sign_file(f, SECRET)
    result = verify_file(f, manifest, "wrongsecret")
    assert not result.ok


# ---------------------------------------------------------------------------
# JSON round-trip
# ---------------------------------------------------------------------------

def test_manifest_json_roundtrip():
    f = _file(_entry("A", "1"), _entry("B", "2"))
    manifest = sign_file(f, SECRET)
    restored = SignatureManifest.from_json(manifest.to_json())
    assert restored.file_digest == manifest.file_digest
    assert len(restored.entries) == len(manifest.entries)


# ---------------------------------------------------------------------------
# format helpers
# ---------------------------------------------------------------------------

def test_format_sign_saved_no_colour():
    f = _file(_entry("A", "1"), _entry("B", "2"))
    manifest = sign_file(f, SECRET)
    text = format_sign_saved(".env.sig", manifest, colour=False)
    assert "Manifest saved" in text
    assert "2 keys" in text
    assert ".env.sig" in text


def test_format_sign_saved_singular():
    f = _file(_entry("A", "1"))
    manifest = sign_file(f, SECRET)
    text = format_sign_saved(".env.sig", manifest, colour=False)
    assert "1 key signed" in text


def test_format_verify_ok_no_colour():
    f = _file(_entry("K", "v"))
    manifest = sign_file(f, SECRET)
    result = verify_file(f, manifest, SECRET)
    text = format_verify_result(result, colour=False)
    assert "valid" in text.lower()


def test_format_verify_failed_lists_keys():
    f = _file(_entry("A", "original"))
    manifest = sign_file(f, SECRET)
    tampered = _file(_entry("A", "modified"))
    result = verify_file(tampered, manifest, SECRET)
    text = format_verify_result(result, colour=False)
    assert "FAILED" in text
    assert "A" in text


def test_format_verify_with_colour_contains_ansi():
    result = VerifyResult(ok=False, tampered_keys=["X"], file_digest_ok=False)
    text = format_verify_result(result, colour=True)
    assert "\033[" in text

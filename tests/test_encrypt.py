"""Tests for envpatch.encrypt."""

from __future__ import annotations

import pytest

from envpatch.parser import EnvEntry, EnvFile

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

try:
    from cryptography.fernet import Fernet

    _KEY: bytes = Fernet.generate_key()
    _HAS_CRYPTO = True
except ImportError:  # pragma: no cover
    _HAS_CRYPTO = False

pytestmark = pytest.mark.skipif(
    not _HAS_CRYPTO, reason="cryptography package not installed"
)

from envpatch.encrypt import (  # noqa: E402  (after skipif guard)
    EncryptResult,
    decrypt_file,
    decrypt_value,
    encrypt_file,
    encrypt_value,
    is_encrypted,
)


def _entry(key: str, value: str, *, comment: bool = False) -> EnvEntry:
    raw = f"# {value}" if comment else f"{key}={value}"
    return EnvEntry(key=None if comment else key, value=value, is_comment=comment, raw=raw)


def _file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


# ---------------------------------------------------------------------------
# encrypt_value / decrypt_value
# ---------------------------------------------------------------------------


def test_encrypt_value_adds_prefix():
    result = encrypt_value("s3cr3t", _KEY)
    assert result.startswith("enc:")


def test_decrypt_value_roundtrip():
    cipher = encrypt_value("hello world", _KEY)
    assert decrypt_value(cipher, _KEY) == "hello world"


def test_decrypt_value_raises_on_missing_prefix():
    with pytest.raises(ValueError, match="enc:"):
        decrypt_value("not-encrypted", _KEY)


def test_is_encrypted_true_for_enc_prefix():
    assert is_encrypted("enc:sometoken") is True


def test_is_encrypted_false_for_plain():
    assert is_encrypted("plaintext") is False


# ---------------------------------------------------------------------------
# encrypt_file
# ---------------------------------------------------------------------------


def test_encrypt_file_encrypts_secret_keys():
    f = _file(_entry("SECRET_KEY", "topsecret"), _entry("APP_NAME", "myapp"))
    result = encrypt_file(f, _KEY)
    entries = {e.key: e.value for e in result.file.entries if e.key}
    assert is_encrypted(entries["SECRET_KEY"])
    assert not is_encrypted(entries["APP_NAME"])


def test_encrypt_file_count_matches():
    f = _file(_entry("API_KEY", "abc"), _entry("TOKEN", "xyz"), _entry("HOST", "localhost"))
    result = encrypt_file(f, _KEY)
    assert result.encrypted_count == 2
    assert result.skipped_count == 1


def test_encrypt_file_only_secrets_false_encrypts_all():
    f = _file(_entry("HOST", "localhost"), _entry("PORT", "5432"))
    result = encrypt_file(f, _KEY, only_secrets=False)
    assert result.encrypted_count == 2


def test_encrypt_file_skips_comments():
    f = _file(_entry("", "a comment line", comment=True), _entry("SECRET", "val"))
    result = encrypt_file(f, _KEY)
    assert result.skipped_count == 1  # comment skipped
    assert result.encrypted_count == 1


def test_encrypt_file_skips_already_encrypted():
    already = encrypt_value("existing", _KEY)
    f = _file(_entry("SECRET_KEY", already))
    result = encrypt_file(f, _KEY)
    assert result.encrypted_count == 0
    assert result.skipped_count == 1


def test_encrypt_result_ok_false_when_nothing_encrypted():
    f = _file(_entry("HOST", "localhost"))  # not a secret key
    result = encrypt_file(f, _KEY)
    assert result.ok() is False


# ---------------------------------------------------------------------------
# decrypt_file
# ---------------------------------------------------------------------------


def test_decrypt_file_roundtrip():
    original = _file(_entry("SECRET_KEY", "mysecret"), _entry("HOST", "localhost"))
    encrypted = encrypt_file(original, _KEY)
    decrypted = decrypt_file(encrypted.file, _KEY)
    values = {e.key: e.value for e in decrypted.entries if e.key}
    assert values["SECRET_KEY"] == "mysecret"
    assert values["HOST"] == "localhost"


def test_decrypt_file_leaves_plain_values_untouched():
    f = _file(_entry("HOST", "localhost"))
    result = decrypt_file(f, _KEY)
    assert result.entries[0].value == "localhost"

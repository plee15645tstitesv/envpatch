"""Symmetric encryption helpers for .env values using Fernet (AES-128-CBC + HMAC).

Allows secrets to be stored encrypted in version-controlled .env files and
decrypted at runtime with a shared key stored outside the repository.
"""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from typing import Optional

from envpatch.parser import EnvEntry, EnvFile, is_secret

_MARKER = "enc:"


def _fernet(key: bytes):
    """Return a Fernet instance; import lazily so cryptography is optional."""
    try:
        from cryptography.fernet import Fernet  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "cryptography package is required for encryption support: "
            "pip install cryptography"
        ) from exc
    return Fernet(key)


def generate_key() -> str:
    """Generate a new URL-safe base-64 encoded 32-byte Fernet key."""
    from cryptography.fernet import Fernet  # type: ignore

    return Fernet.generate_key().decode()


def encrypt_value(plaintext: str, key: bytes) -> str:
    """Encrypt *plaintext* and return a prefixed ciphertext string."""
    token = _fernet(key).encrypt(plaintext.encode()).decode()
    return f"{_MARKER}{token}"


def decrypt_value(value: str, key: bytes) -> str:
    """Decrypt a prefixed ciphertext string and return the plaintext.

    Raises ``ValueError`` if *value* does not carry the expected prefix.
    """
    if not value.startswith(_MARKER):
        raise ValueError(f"Value is not encrypted (missing '{_MARKER}' prefix)")
    token = value[len(_MARKER) :]
    return _fernet(key).decrypt(token.encode()).decode()


def is_encrypted(value: str) -> bool:
    """Return ``True`` when *value* looks like an encrypted token."""
    return value.startswith(_MARKER)


@dataclass
class EncryptResult:
    """Outcome of encrypting an :class:`~envpatch.parser.EnvFile`."""

    file: EnvFile
    encrypted_count: int
    skipped_count: int

    def ok(self) -> bool:  # noqa: D401
        """``True`` when at least one value was encrypted."""
        return self.encrypted_count > 0


def encrypt_file(
    env_file: EnvFile,
    key: bytes,
    *,
    only_secrets: bool = True,
) -> EncryptResult:
    """Return a new :class:`~envpatch.parser.EnvFile` with secret values encrypted.

    Parameters
    ----------
    env_file:
        Source file whose entries will be processed.
    key:
        Fernet key bytes used for encryption.
    only_secrets:
        When ``True`` (default) only keys identified as secrets by
        :func:`~envpatch.parser.is_secret` are encrypted.  Set to ``False``
        to encrypt every non-comment, non-blank entry.
    """
    new_entries: list[EnvEntry] = []
    encrypted = 0
    skipped = 0

    for entry in env_file.entries:
        if entry.is_comment or entry.key is None or is_encrypted(entry.value or ""):
            new_entries.append(entry)
            skipped += 1
            continue

        if only_secrets and not is_secret(entry.key):
            new_entries.append(entry)
            skipped += 1
            continue

        new_value = encrypt_value(entry.value or "", key)
        new_entries.append(
            EnvEntry(
                key=entry.key,
                value=new_value,
                is_comment=False,
                raw=f"{entry.key}={new_value}",
            )
        )
        encrypted += 1

    return EncryptResult(
        file=EnvFile(entries=new_entries),
        encrypted_count=encrypted,
        skipped_count=skipped,
    )


def decrypt_file(env_file: EnvFile, key: bytes) -> EnvFile:
    """Return a new :class:`~envpatch.parser.EnvFile` with all encrypted values decrypted."""
    new_entries: list[EnvEntry] = []
    for entry in env_file.entries:
        if entry.is_comment or entry.key is None or not is_encrypted(entry.value or ""):
            new_entries.append(entry)
            continue
        plain = decrypt_value(entry.value, key)  # type: ignore[arg-type]
        new_entries.append(
            EnvEntry(
                key=entry.key,
                value=plain,
                is_comment=False,
                raw=f"{entry.key}={plain}",
            )
        )
    return EnvFile(entries=new_entries)

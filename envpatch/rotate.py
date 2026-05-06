"""Key rotation: re-encrypt already-encrypted values with a new key."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .encrypt import decrypt_value, encrypt_value, is_encrypted
from .parser import EnvEntry, EnvFile


@dataclass
class RotateResult:
    """Outcome of a key-rotation pass over an EnvFile."""

    rotated: List[str] = field(default_factory=list)   # keys whose values were re-encrypted
    skipped: List[str] = field(default_factory=list)   # keys that were not encrypted
    errors: List[str] = field(default_factory=list)    # keys that failed to rotate
    file: Optional[EnvFile] = None                     # updated file (None on total failure)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0

    @property
    def total_rotated(self) -> int:
        return len(self.rotated)

    @property
    def total_skipped(self) -> int:
        return len(self.skipped)


def rotate(env_file: EnvFile, old_key: str, new_key: str) -> RotateResult:
    """Re-encrypt every encrypted value in *env_file* from *old_key* to *new_key*.

    Non-encrypted entries are left untouched.  Comment and blank entries are
    passed through unchanged.  Returns a :class:`RotateResult` that includes
    the updated :class:`EnvFile`.
    """
    result = RotateResult()
    new_entries: List[EnvEntry] = []

    for entry in env_file.entries:
        if entry.is_comment or entry.key is None:
            new_entries.append(entry)
            continue

        if not is_encrypted(entry.value or ""):
            result.skipped.append(entry.key)
            new_entries.append(entry)
            continue

        try:
            plaintext = decrypt_value(entry.value or "", old_key)
            new_ciphertext = encrypt_value(plaintext, new_key)
            new_entries.append(
                EnvEntry(
                    key=entry.key,
                    value=new_ciphertext,
                    is_comment=entry.is_comment,
                    raw=f"{entry.key}={new_ciphertext}",
                )
            )
            result.rotated.append(entry.key)
        except Exception as exc:  # noqa: BLE001
            result.errors.append(entry.key)
            new_entries.append(entry)  # keep original on error

    result.file = EnvFile(entries=new_entries)
    return result

"""Mask: selectively obscure values in an EnvFile for safe display or logging."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .parser import EnvEntry, EnvFile, is_secret

_MASK_CHAR = "*"
_DEFAULT_VISIBLE = 4


@dataclass
class MaskResult:
    """Outcome of a mask operation."""
    entries: List[EnvEntry] = field(default_factory=list)
    total_masked: int = 0
    total_visible: int = 0

    def ok(self) -> bool:
        return True

    def as_env_file(self) -> EnvFile:
        return EnvFile(entries=self.entries)


def _mask_value(value: str, visible_chars: int, mask_char: str) -> str:
    """Return a masked version of *value*, keeping the last *visible_chars* characters."""
    if not value:
        return value
    if visible_chars <= 0 or len(value) <= visible_chars:
        return mask_char * max(len(value), 4)
    tail = value[-visible_chars:]
    return mask_char * (len(value) - visible_chars) + tail


def mask(
    env_file: EnvFile,
    *,
    keys: Optional[List[str]] = None,
    secrets_only: bool = True,
    visible_chars: int = _DEFAULT_VISIBLE,
    mask_char: str = _MASK_CHAR,
) -> MaskResult:
    """Return a :class:`MaskResult` where qualifying values are masked.

    Parameters
    ----------
    env_file:
        The source file to process.
    keys:
        Explicit list of keys to mask. If *None* and *secrets_only* is
        ``True``, all secret-looking keys are masked.
    secrets_only:
        When *True* (default) and *keys* is *None*, only keys detected as
        secrets by :func:`~envpatch.parser.is_secret` are masked.
    visible_chars:
        Number of trailing characters to leave unmasked (default 4).
    mask_char:
        Character used for masking (default ``'*'``).
    """
    key_set = set(keys) if keys is not None else None
    masked_entries: List[EnvEntry] = []
    total_masked = 0
    total_visible = 0

    for entry in env_file.entries:
        if entry.comment or entry.key is None:
            masked_entries.append(entry)
            continue

        should_mask = (
            (key_set is not None and entry.key in key_set)
            or (key_set is None and secrets_only and is_secret(entry.key))
        )

        if should_mask:
            masked_value = _mask_value(entry.value or "", visible_chars, mask_char)
            masked_entries.append(
                EnvEntry(
                    key=entry.key,
                    value=masked_value,
                    comment=entry.comment,
                    raw=entry.raw,
                )
            )
            total_masked += 1
        else:
            masked_entries.append(entry)
            total_visible += 1

    return MaskResult(
        entries=masked_entries,
        total_masked=total_masked,
        total_visible=total_visible,
    )

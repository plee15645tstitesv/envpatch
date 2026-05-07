"""Pin specific env keys to fixed values, preventing them from being overwritten by merges or patches."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envpatch.parser import EnvFile, EnvEntry


@dataclass
class PinEntry:
    key: str
    value: str
    reason: Optional[str] = None

    def as_dict(self) -> dict:
        d: dict = {"key": self.key, "value": self.value}
        if self.reason:
            d["reason"] = self.reason
        return d


@dataclass
class PinResult:
    pinned: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    file: Optional[EnvFile] = None

    @property
    def ok(self) -> bool:
        return True

    @property
    def total_pinned(self) -> int:
        return len(self.pinned)

    @property
    def total_skipped(self) -> int:
        return len(self.skipped)


def apply_pins(
    env: EnvFile,
    pins: Dict[str, PinEntry],
    *,
    overwrite: bool = True,
) -> PinResult:
    """Apply a set of pinned key→value pairs to *env*.

    Args:
        env: The base :class:`EnvFile` to update.
        pins: Mapping of key name to :class:`PinEntry`.
        overwrite: When *True* (default) existing keys are overwritten with the
            pinned value.  When *False* only keys absent from *env* are set.

    Returns:
        A :class:`PinResult` whose ``.file`` holds the updated :class:`EnvFile`.
    """
    result = PinResult()
    existing: Dict[str, int] = {}
    for idx, entry in enumerate(env.entries):
        if entry.key:
            existing[entry.key] = idx

    new_entries: List[EnvEntry] = list(env.entries)

    for key, pin in pins.items():
        if key in existing:
            if overwrite:
                old = new_entries[existing[key]]
                new_entries[existing[key]] = EnvEntry(
                    key=old.key,
                    value=pin.value,
                    comment=old.comment,
                    is_comment=old.is_comment,
                )
                result.pinned.append(key)
            else:
                result.skipped.append(key)
        else:
            new_entries.append(
                EnvEntry(key=key, value=pin.value, comment=False, is_comment=False)
            )
            result.pinned.append(key)

    result.file = EnvFile(entries=new_entries)
    return result

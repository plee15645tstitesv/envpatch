"""Resolve missing keys in a target env file using a reference env file."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .parser import EnvFile, EnvEntry
from .redact import redact_entry


@dataclass
class ResolveResult:
    """Outcome of a resolve operation."""

    source_env: str
    target_env: str
    filled: List[EnvEntry] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    output: Optional[EnvFile] = None

    def ok(self) -> bool:
        """True when at least one key was resolved (or nothing was missing)."""
        return True

    def total_filled(self) -> int:
        return len(self.filled)

    def total_skipped(self) -> int:
        return len(self.skipped)


def resolve(
    source: EnvFile,
    target: EnvFile,
    *,
    source_env: str = "source",
    target_env: str = "target",
    redact_secrets: bool = True,
    overwrite_existing: bool = False,
) -> ResolveResult:
    """Fill missing keys in *target* using values from *source*.

    Parameters
    ----------
    source:
        The reference :class:`EnvFile` that provides values.
    target:
        The :class:`EnvFile` to be completed.
    source_env:
        Human-readable label for the source environment.
    target_env:
        Human-readable label for the target environment.
    redact_secrets:
        When *True* (default) secret values from *source* are replaced with
        an empty string in the resolved output so they are never leaked.
    overwrite_existing:
        When *True*, keys already present in *target* are also updated from
        *source*.  Defaults to *False* (only missing keys are added).
    """
    target_keys = {
        e.key for e in target.entries if e.key is not None
    }
    source_map = {
        e.key: e for e in source.entries if e.key is not None
    }

    filled: List[EnvEntry] = []
    skipped: List[str] = []
    new_entries = list(target.entries)

    for key, src_entry in source_map.items():
        if key in target_keys and not overwrite_existing:
            skipped.append(key)
            continue

        resolved = redact_entry(src_entry) if redact_secrets else src_entry

        if key in target_keys and overwrite_existing:
            # Replace in-place
            new_entries = [
                resolved if (e.key == key) else e for e in new_entries
            ]
        else:
            new_entries.append(resolved)

        filled.append(resolved)

    output = EnvFile(entries=new_entries)
    return ResolveResult(
        source_env=source_env,
        target_env=target_env,
        filled=filled,
        skipped=skipped,
        output=output,
    )

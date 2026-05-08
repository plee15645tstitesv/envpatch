"""Flatten multiple EnvFile layers into a single resolved mapping.

Similar to chain but produces a flat dict with provenance metadata,
useful for debugging which file contributed each final value.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envpatch.parser import EnvFile, EnvEntry


@dataclass
class FlattenEntry:
    key: str
    value: str
    source: str          # label / filename of the winning file
    overridden_by: Optional[str] = None  # set on losers; points to winner label

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "source": self.source,
            "overridden_by": self.overridden_by,
        }


@dataclass
class FlattenResult:
    entries: List[FlattenEntry] = field(default_factory=list)
    # all entries including losers, keyed by key then source
    provenance: Dict[str, List[FlattenEntry]] = field(default_factory=dict)

    def ok(self) -> bool:
        return True

    def as_dict(self) -> dict:
        return {
            "entries": [e.as_dict() for e in self.entries],
            "provenance": {
                k: [e.as_dict() for e in vs]
                for k, vs in self.provenance.items()
            },
        }

    def winner(self, key: str) -> Optional[FlattenEntry]:
        """Return the winning (final) entry for *key*, or None."""
        for e in self.entries:
            if e.key == key:
                return e
        return None

    def sources_for(self, key: str) -> List[str]:
        """Return all source labels that defined *key*, in layer order."""
        return [e.source for e in self.provenance.get(key, [])]


def flatten(
    layers: List[tuple[str, EnvFile]],
    *,
    skip_secrets: bool = False,
) -> FlattenResult:
    """Flatten *layers* (label, EnvFile) pairs, later layers win.

    Args:
        layers:       Ordered sequence of (label, EnvFile) pairs.
                      Earlier entries are base; later entries override.
        skip_secrets: When True, secret keys are excluded from the result.

    Returns:
        A :class:`FlattenResult` with the winning entries and full provenance.
    """
    # key -> list of FlattenEntry in layer order
    provenance: Dict[str, List[FlattenEntry]] = {}

    for label, env_file in layers:
        for entry in env_file.entries:
            if entry.is_comment:
                continue
            if skip_secrets and entry.is_secret:
                continue
            fe = FlattenEntry(key=entry.key, value=entry.value, source=label)
            provenance.setdefault(entry.key, []).append(fe)

    # Determine winners and annotate losers
    winning_entries: List[FlattenEntry] = []
    # preserve insertion order of first-seen keys
    seen_order: List[str] = []
    for label, env_file in layers:
        for entry in env_file.entries:
            if entry.is_comment:
                continue
            if skip_secrets and entry.is_secret:
                continue
            if entry.key not in seen_order:
                seen_order.append(entry.key)

    for key in seen_order:
        all_for_key = provenance[key]
        winner = all_for_key[-1]  # last layer wins
        for loser in all_for_key[:-1]:
            loser.overridden_by = winner.source
        winning_entries.append(winner)

    return FlattenResult(entries=winning_entries, provenance=provenance)

"""Tag .env entries with arbitrary labels for grouping and filtering."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envpatch.parser import EnvEntry, EnvFile


@dataclass
class TagEntry:
    key: str
    tags: List[str]

    def as_dict(self) -> dict:
        return {"key": self.key, "tags": sorted(self.tags)}


@dataclass
class TagResult:
    tagged: List[TagEntry] = field(default_factory=list)
    untagged_keys: List[str] = field(default_factory=list)

    def ok(self) -> bool:
        return True

    def total_tagged(self) -> int:
        return len(self.tagged)

    def total_untagged(self) -> int:
        return len(self.untagged_keys)

    def keys_for_tag(self, tag: str) -> List[str]:
        """Return all keys that carry *tag*."""
        return [e.key for e in self.tagged if tag in e.tags]

    def as_env_file(self, tag: str, source: EnvFile) -> EnvFile:
        """Return a new EnvFile containing only entries whose key carries *tag*."""
        wanted = set(self.keys_for_tag(tag))
        entries = [e for e in source.entries if not e.comment and e.key in wanted]
        return EnvFile(entries=entries)


def tag(
    env_file: EnvFile,
    tag_map: Dict[str, List[str]],
) -> TagResult:
    """Assign tags to entries in *env_file* according to *tag_map*.

    *tag_map* maps a tag label to a list of key patterns (exact match for now).
    Keys not covered by any tag are collected in ``untagged_keys``.
    """
    # Build reverse map: key -> set of tags
    key_to_tags: Dict[str, List[str]] = {}
    for label, keys in tag_map.items():
        for k in keys:
            key_to_tags.setdefault(k, []).append(label)

    result = TagResult()
    for entry in env_file.entries:
        if entry.comment:
            continue
        if entry.key in key_to_tags:
            result.tagged.append(TagEntry(key=entry.key, tags=key_to_tags[entry.key]))
        else:
            result.untagged_keys.append(entry.key)
    return result

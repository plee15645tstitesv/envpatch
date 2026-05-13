"""Split a single .env file into multiple files by key prefix."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .parser import EnvEntry, EnvFile


@dataclass
class SplitResult:
    ok: bool
    source_env: str
    buckets: Dict[str, EnvFile] = field(default_factory=dict)
    unmatched: EnvFile = field(default_factory=lambda: EnvFile(entries=[]))
    total_keys: int = 0
    total_unmatched: int = 0

    def bucket_names(self) -> List[str]:
        return list(self.buckets.keys())


def split(
    source: EnvFile,
    prefixes: List[str],
    *,
    strip_prefix: bool = False,
    include_comments: bool = False,
    source_env: str = "source",
) -> SplitResult:
    """Split *source* into one EnvFile per prefix bucket.

    Keys are placed in the first matching bucket.  Keys that match no
    prefix land in ``result.unmatched``.

    Args:
        source: The env file to split.
        prefixes: Ordered list of prefix strings to match against key names.
        strip_prefix: When True, remove the matched prefix from the key name
            in the output file.
        include_comments: When True, copy comment/blank entries into every
            bucket that receives at least one key.
        source_env: Label used in the returned result for reporting.

    Returns:
        A :class:`SplitResult` describing the split.
    """
    buckets: Dict[str, List[EnvEntry]] = {p: [] for p in prefixes}
    unmatched: List[EnvEntry] = []
    comments: List[EnvEntry] = []
    total_keys = 0
    total_unmatched = 0

    for entry in source.entries:
        if entry.comment:
            comments.append(entry)
            continue

        matched = False
        for prefix in prefixes:
            if entry.key.startswith(prefix):
                new_key = entry.key[len(prefix):] if strip_prefix else entry.key
                buckets[prefix].append(
                    EnvEntry(
                        key=new_key,
                        value=entry.value,
                        comment=entry.comment,
                        raw=entry.raw,
                    )
                )
                total_keys += 1
                matched = True
                break

        if not matched:
            unmatched.append(entry)
            total_unmatched += 1

    result_buckets: Dict[str, EnvFile] = {}
    for prefix, entries in buckets.items():
        if include_comments and entries:
            all_entries = comments + entries
        else:
            all_entries = entries
        result_buckets[prefix] = EnvFile(entries=all_entries)

    unmatched_file = EnvFile(
        entries=(comments + unmatched) if include_comments and unmatched else unmatched
    )

    return SplitResult(
        ok=True,
        source_env=source_env,
        buckets=result_buckets,
        unmatched=unmatched_file,
        total_keys=total_keys,
        total_unmatched=total_unmatched,
    )

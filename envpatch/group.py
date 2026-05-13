"""Group .env entries by a shared key prefix into named buckets."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envpatch.parser import EnvEntry, EnvFile


@dataclass
class GroupResult:
    source_env: str
    prefix_sep: str
    groups: Dict[str, List[EnvEntry]] = field(default_factory=dict)
    ungrouped: List[EnvEntry] = field(default_factory=list)

    def ok(self) -> bool:
        return True

    def total_grouped(self) -> int:
        return sum(len(v) for v in self.groups.values())

    def total_ungrouped(self) -> int:
        return len(self.ungrouped)

    def as_env_file(self, group_name: str) -> Optional[EnvFile]:
        """Return a synthetic EnvFile containing only entries from *group_name*."""
        if group_name not in self.groups:
            return None
        return EnvFile(env=group_name, entries=list(self.groups[group_name]))

    def group_names(self) -> List[str]:
        return sorted(self.groups.keys())


def group(
    env_file: EnvFile,
    prefix_sep: str = "_",
    include_comments: bool = False,
) -> GroupResult:
    """Partition *env_file* entries by the first segment of their key.

    Keys that contain *prefix_sep* are placed in the bucket named after the
    text before the first separator.  Keys with no separator land in
    ``ungrouped``.

    Parameters
    ----------
    env_file:
        Source file to group.
    prefix_sep:
        Separator character used to split key names (default ``"_"``).
    include_comments:
        When *True*, comment/blank entries are attached to the same bucket as
        the entry immediately following them.  When *False* they are dropped.
    """
    result = GroupResult(source_env=env_file.env, prefix_sep=prefix_sep)

    pending_comments: List[EnvEntry] = []

    for entry in env_file.entries:
        if entry.comment:
            if include_comments:
                pending_comments.append(entry)
            continue

        if prefix_sep in entry.key:
            bucket = entry.key.split(prefix_sep, 1)[0]
            if bucket not in result.groups:
                result.groups[bucket] = []
            if include_comments:
                result.groups[bucket].extend(pending_comments)
                pending_comments = []
            result.groups[bucket].append(entry)
        else:
            if include_comments:
                result.ungrouped.extend(pending_comments)
                pending_comments = []
            result.ungrouped.append(entry)

    return result

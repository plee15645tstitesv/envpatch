"""Compare two env files and produce a structured summary report."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envpatch.parser import EnvFile
from envpatch.diff import diff, ChangeType, DiffEntry


@dataclass
class CompareReport:
    """High-level comparison summary between two EnvFile instances."""

    source_name: str
    target_name: str
    added: List[DiffEntry] = field(default_factory=list)
    removed: List[DiffEntry] = field(default_factory=list)
    modified: List[DiffEntry] = field(default_factory=list)
    unchanged: List[DiffEntry] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """True when source and target are identical (no changes)."""
        return not (self.added or self.removed or self.modified)

    @property
    def total_changes(self) -> int:
        return len(self.added) + len(self.removed) + len(self.modified)

    def changed_keys(self) -> List[str]:
        """Return sorted list of keys that differ between the two files."""
        keys = (
            [e.key for e in self.added]
            + [e.key for e in self.removed]
            + [e.key for e in self.modified]
        )
        return sorted(set(keys))


def compare(
    source: EnvFile,
    target: EnvFile,
    source_name: str = "source",
    target_name: str = "target",
) -> CompareReport:
    """Diff *source* against *target* and bucket entries by change type.

    Parameters
    ----------
    source:
        The baseline env file (e.g. ``.env.example``).
    target:
        The env file being compared (e.g. ``.env.production``).
    source_name:
        Human-readable label for *source* used in the report.
    target_name:
        Human-readable label for *target* used in the report.
    """
    entries = diff(source, target)
    report = CompareReport(source_name=source_name, target_name=target_name)

    for entry in entries:
        if entry.change == ChangeType.ADDED:
            report.added.append(entry)
        elif entry.change == ChangeType.REMOVED:
            report.removed.append(entry)
        elif entry.change == ChangeType.MODIFIED:
            report.modified.append(entry)
        else:
            report.unchanged.append(entry)

    return report

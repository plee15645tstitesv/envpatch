"""Audit log: record diff/merge operations with timestamps and metadata."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

_DEFAULT_AUDIT_FILE = ".envpatch_audit.jsonl"


@dataclass
class AuditEntry:
    operation: str          # "diff" | "merge" | "validate" | "schema"
    base_file: str
    patch_file: Optional[str]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    keys_added: int = 0
    keys_removed: int = 0
    keys_modified: int = 0
    keys_unchanged: int = 0
    had_conflicts: bool = False
    note: str = ""

    def as_dict(self) -> dict:
        return {
            "operation": self.operation,
            "base_file": self.base_file,
            "patch_file": self.patch_file,
            "timestamp": self.timestamp,
            "keys_added": self.keys_added,
            "keys_removed": self.keys_removed,
            "keys_modified": self.keys_modified,
            "keys_unchanged": self.keys_unchanged,
            "had_conflicts": self.had_conflicts,
            "note": self.note,
        }


def _audit_path(directory: str = ".") -> Path:
    return Path(directory) / _DEFAULT_AUDIT_FILE


def append_entry(entry: AuditEntry, directory: str = ".") -> Path:
    """Append a single audit entry as a JSON line."""
    path = _audit_path(directory)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry.as_dict()) + "\n")
    return path


def load_entries(directory: str = ".") -> List[AuditEntry]:
    """Load all audit entries from the JSONL file."""
    path = _audit_path(directory)
    if not path.exists():
        return []
    entries: List[AuditEntry] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            entries.append(AuditEntry(**data))
    return entries


def clear_audit_log(directory: str = ".") -> bool:
    """Delete the audit log. Returns True if it existed."""
    path = _audit_path(directory)
    if path.exists():
        path.unlink()
        return True
    return False

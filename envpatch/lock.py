"""Lock file support: record a frozen snapshot of key names and their
secret-status so CI can detect unexpected schema drift."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from envpatch.parser import EnvFile, is_secret

_LOCK_FILENAME = ".env.lock"


@dataclass
class LockEntry:
    key: str
    secret: bool

    def as_dict(self) -> dict:
        return {"key": self.key, "secret": self.secret}


@dataclass
class LockFile:
    entries: List[LockEntry] = field(default_factory=list)

    def keys(self) -> List[str]:
        return [e.key for e in self.entries]

    def as_dict(self) -> Dict[str, bool]:
        return {e.key: e.secret for e in self.entries}


@dataclass
class LockDrift:
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    secret_changed: List[str] = field(default_factory=list)

    def ok(self) -> bool:
        return not (self.added or self.removed or self.secret_changed)


def _lock_path(directory: str = ".") -> Path:
    return Path(directory) / _LOCK_FILENAME


def generate_lock(env_file: EnvFile) -> LockFile:
    """Build a LockFile from the live entries in *env_file*."""
    entries = [
        LockEntry(key=e.key, secret=is_secret(e.key))
        for e in env_file.entries
        if not e.is_comment and e.key
    ]
    return LockFile(entries=entries)


def save_lock(lock: LockFile, directory: str = ".") -> Path:
    """Serialise *lock* to JSON and write it to *directory*."""
    path = _lock_path(directory)
    payload = [e.as_dict() for e in lock.entries]
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def load_lock(directory: str = ".") -> LockFile:
    """Read and deserialise the lock file from *directory*."""
    path = _lock_path(directory)
    if not path.exists():
        raise FileNotFoundError(f"Lock file not found: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    entries = [LockEntry(key=item["key"], secret=item["secret"]) for item in raw]
    return LockFile(entries=entries)


def check_drift(env_file: EnvFile, lock: LockFile) -> LockDrift:
    """Compare *env_file* against *lock* and report any drift."""
    live = generate_lock(env_file)
    live_map = live.as_dict()
    lock_map = lock.as_dict()

    added = [k for k in live_map if k not in lock_map]
    removed = [k for k in lock_map if k not in live_map]
    secret_changed = [
        k for k in live_map if k in lock_map and live_map[k] != lock_map[k]
    ]
    return LockDrift(added=added, removed=removed, secret_changed=secret_changed)

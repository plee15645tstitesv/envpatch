"""Snapshot support: save and load named .env snapshots for later diffing."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from envpatch.parser import EnvFile, EnvEntry

DEFAULT_SNAPSHOT_DIR = Path(".envpatch_snapshots")


def _snapshot_path(name: str, directory: Path) -> Path:
    return directory / f"{name}.json"


def save_snapshot(
    env_file: EnvFile,
    name: str,
    directory: Path = DEFAULT_SNAPSHOT_DIR,
) -> Path:
    """Persist *env_file* as a named snapshot under *directory*."""
    directory.mkdir(parents=True, exist_ok=True)
    path = _snapshot_path(name, directory)
    payload = {
        "name": name,
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "entries": [
            {
                "key": e.key,
                "value": e.value,
                "comment": e.comment,
                "raw": e.raw,
            }
            for e in env_file.entries
        ],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def load_snapshot(
    name: str,
    directory: Path = DEFAULT_SNAPSHOT_DIR,
) -> EnvFile:
    """Load a previously saved snapshot and return it as an :class:`EnvFile`."""
    path = _snapshot_path(name, directory)
    if not path.exists():
        raise FileNotFoundError(f"Snapshot '{name}' not found at {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    entries: List[EnvEntry] = [
        EnvEntry(
            key=e["key"],
            value=e["value"],
            comment=e["comment"],
            raw=e["raw"],
        )
        for e in payload["entries"]
    ]
    return EnvFile(entries=entries)


def list_snapshots(directory: Path = DEFAULT_SNAPSHOT_DIR) -> List[str]:
    """Return sorted snapshot names available in *directory*."""
    if not directory.exists():
        return []
    return sorted(
        p.stem for p in directory.iterdir() if p.suffix == ".json"
    )


def delete_snapshot(
    name: str,
    directory: Path = DEFAULT_SNAPSHOT_DIR,
) -> None:
    """Remove a named snapshot; raises FileNotFoundError if absent."""
    path = _snapshot_path(name, directory)
    if not path.exists():
        raise FileNotFoundError(f"Snapshot '{name}' not found at {path}")
    path.unlink()

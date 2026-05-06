"""Profile management: named sets of env overrides per environment."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envpatch.parser import EnvFile, EnvEntry


@dataclass
class Profile:
    name: str
    env: str
    overrides: Dict[str, str] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {"name": self.name, "env": self.env, "overrides": self.overrides}


@dataclass
class ProfileStore:
    profiles: List[Profile] = field(default_factory=list)

    def names(self) -> List[str]:
        return [p.name for p in self.profiles]

    def get(self, name: str) -> Optional[Profile]:
        for p in self.profiles:
            if p.name == name:
                return p
        return None

    def add(self, profile: Profile) -> None:
        existing = self.get(profile.name)
        if existing is not None:
            self.profiles.remove(existing)
        self.profiles.append(profile)

    def remove(self, name: str) -> bool:
        profile = self.get(name)
        if profile is None:
            return False
        self.profiles.remove(profile)
        return True


def _profile_path(directory: Path) -> Path:
    return directory / ".envpatch_profiles.json"


def save_profiles(store: ProfileStore, directory: Path) -> Path:
    path = _profile_path(directory)
    path.write_text(json.dumps([p.as_dict() for p in store.profiles], indent=2))
    return path


def load_profiles(directory: Path) -> ProfileStore:
    path = _profile_path(directory)
    if not path.exists():
        return ProfileStore()
    data = json.loads(path.read_text())
    profiles = [Profile(name=d["name"], env=d["env"], overrides=d["overrides"]) for d in data]
    return ProfileStore(profiles=profiles)


def apply_profile(base: EnvFile, profile: Profile) -> EnvFile:
    """Return a new EnvFile with profile overrides applied."""
    new_entries: List[EnvEntry] = []
    overrides = dict(profile.overrides)

    for entry in base.entries:
        if entry.is_comment or entry.key is None:
            new_entries.append(entry)
        elif entry.key in overrides:
            new_entries.append(EnvEntry(
                raw=f"{entry.key}={overrides.pop(entry.key)}",
                key=entry.key,
                value=overrides.get(entry.key, entry.value),
                is_comment=False,
            ))
        else:
            new_entries.append(entry)

    for key, value in overrides.items():
        new_entries.append(EnvEntry(
            raw=f"{key}={value}",
            key=key,
            value=value,
            is_comment=False,
        ))

    return EnvFile(entries=new_entries)

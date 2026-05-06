"""Formatting helpers for profile commands."""
from __future__ import annotations

from typing import List

from envpatch.profile import Profile, ProfileStore

_ANSI_GREEN = "\033[32m"
_ANSI_YELLOW = "\033[33m"
_ANSI_RED = "\033[31m"
_ANSI_RESET = "\033[0m"


def _c(text: str, code: str, colour: bool) -> str:
    return f"{code}{text}{_ANSI_RESET}" if colour else text


def format_profile_list(store: ProfileStore, *, colour: bool = False) -> str:
    if not store.profiles:
        return "No profiles saved."
    lines = []
    for p in store.profiles:
        name = _c(p.name, _ANSI_GREEN, colour)
        env = _c(p.env, _ANSI_YELLOW, colour)
        count = len(p.overrides)
        lines.append(f"  {name}  [{env}]  {count} override(s)")
    return "\n".join(lines)


def format_profile_saved(profile: Profile, *, colour: bool = False) -> str:
    name = _c(profile.name, _ANSI_GREEN, colour)
    return f"Profile {name} saved ({len(profile.overrides)} override(s))."


def format_profile_deleted(name: str, *, colour: bool = False) -> str:
    label = _c(name, _ANSI_RED, colour)
    return f"Profile {label} deleted."


def format_profile_not_found(name: str, *, colour: bool = False) -> str:
    label = _c(name, _ANSI_RED, colour)
    return f"Profile {label} not found."


def format_profile_applied(profile: Profile, key_count: int, *, colour: bool = False) -> str:
    name = _c(profile.name, _ANSI_GREEN, colour)
    env = _c(profile.env, _ANSI_YELLOW, colour)
    return f"Applied profile {name} [{env}]: {key_count} key(s) in result."

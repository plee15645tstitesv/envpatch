"""Tests for envpatch.profile."""
from __future__ import annotations

import pytest
from pathlib import Path

from envpatch.parser import EnvEntry, EnvFile
from envpatch.profile import (
    Profile,
    ProfileStore,
    apply_profile,
    save_profiles,
    load_profiles,
)


def _entry(key: str, value: str) -> EnvEntry:
    return EnvEntry(raw=f"{key}={value}", key=key, value=value, is_comment=False)


def _file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


def _profile(name: str = "test", env: str = "staging", **overrides: str) -> Profile:
    return Profile(name=name, env=env, overrides=dict(overrides))


# --- ProfileStore ---

def test_store_names_empty():
    assert ProfileStore().names() == []


def test_store_add_and_get():
    store = ProfileStore()
    p = _profile("dev", "development", FOO="bar")
    store.add(p)
    assert store.get("dev") is p


def test_store_add_replaces_existing():
    store = ProfileStore()
    store.add(_profile("dev", "development", FOO="old"))
    store.add(_profile("dev", "development", FOO="new"))
    assert len(store.profiles) == 1
    assert store.get("dev").overrides["FOO"] == "new"


def test_store_remove_existing():
    store = ProfileStore()
    store.add(_profile("dev"))
    result = store.remove("dev")
    assert result is True
    assert store.get("dev") is None


def test_store_remove_missing_returns_false():
    store = ProfileStore()
    assert store.remove("ghost") is False


# --- save / load ---

def test_save_creates_file(tmp_path):
    store = ProfileStore(profiles=[_profile("ci", "ci", SECRET="x")])
    path = save_profiles(store, tmp_path)
    assert path.exists()


def test_load_roundtrip(tmp_path):
    store = ProfileStore(profiles=[_profile("ci", "ci", KEY="val")])
    save_profiles(store, tmp_path)
    loaded = load_profiles(tmp_path)
    assert loaded.names() == ["ci"]
    assert loaded.get("ci").overrides == {"KEY": "val"}


def test_load_missing_returns_empty_store(tmp_path):
    store = load_profiles(tmp_path)
    assert store.profiles == []


# --- apply_profile ---

def test_apply_profile_overrides_existing_key():
    base = _file(_entry("DB_HOST", "localhost"))
    profile = _profile("staging", "staging", DB_HOST="prod.db")
    result = apply_profile(base, profile)
    vals = {e.key: e.value for e in result.entries if e.key}
    assert vals["DB_HOST"] == "prod.db"


def test_apply_profile_adds_missing_key():
    base = _file(_entry("FOO", "bar"))
    profile = _profile("staging", "staging", NEW_KEY="new_val")
    result = apply_profile(base, profile)
    vals = {e.key: e.value for e in result.entries if e.key}
    assert "NEW_KEY" in vals


def test_apply_profile_preserves_non_overridden_keys():
    base = _file(_entry("KEEP", "me"), _entry("CHANGE", "old"))
    profile = _profile("p", "env", CHANGE="new")
    result = apply_profile(base, profile)
    vals = {e.key: e.value for e in result.entries if e.key}
    assert vals["KEEP"] == "me"


def test_apply_profile_preserves_comments():
    comment = EnvEntry(raw="# comment", key=None, value=None, is_comment=True)
    base = EnvFile(entries=[comment, _entry("X", "1")])
    profile = _profile("p", "env", X="2")
    result = apply_profile(base, profile)
    assert result.entries[0].is_comment is True

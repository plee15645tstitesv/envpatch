"""Tests for envpatch.snapshot."""

from __future__ import annotations

import pytest
from pathlib import Path

from envpatch.parser import EnvEntry, EnvFile
from envpatch.snapshot import (
    save_snapshot,
    load_snapshot,
    list_snapshots,
    delete_snapshot,
)


def _make_file(*pairs) -> EnvFile:
    entries = [
        EnvEntry(key=k, value=v, comment=False, raw=f"{k}={v}")
        for k, v in pairs
    ]
    return EnvFile(entries=entries)


def test_save_creates_file(tmp_path):
    env = _make_file(("FOO", "bar"), ("BAZ", "qux"))
    out = save_snapshot(env, "prod", directory=tmp_path)
    assert out.exists()
    assert out.name == "prod.json"


def test_load_roundtrip(tmp_path):
    env = _make_file(("HOST", "localhost"), ("PORT", "5432"))
    save_snapshot(env, "dev", directory=tmp_path)
    loaded = load_snapshot("dev", directory=tmp_path)
    assert len(loaded.entries) == 2
    assert loaded.entries[0].key == "HOST"
    assert loaded.entries[0].value == "localhost"
    assert loaded.entries[1].key == "PORT"
    assert loaded.entries[1].value == "5432"


def test_load_preserves_comment_flag(tmp_path):
    entries = [
        EnvEntry(key=None, value=None, comment=True, raw="# a comment"),
        EnvEntry(key="X", value="1", comment=False, raw="X=1"),
    ]
    env = EnvFile(entries=entries)
    save_snapshot(env, "snap", directory=tmp_path)
    loaded = load_snapshot("snap", directory=tmp_path)
    assert loaded.entries[0].comment is True
    assert loaded.entries[1].key == "X"


def test_load_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError, match="ghost"):
        load_snapshot("ghost", directory=tmp_path)


def test_list_snapshots_empty(tmp_path):
    assert list_snapshots(directory=tmp_path) == []


def test_list_snapshots_returns_names(tmp_path):
    env = _make_file(("A", "1"))
    save_snapshot(env, "alpha", directory=tmp_path)
    save_snapshot(env, "beta", directory=tmp_path)
    save_snapshot(env, "gamma", directory=tmp_path)
    assert list_snapshots(directory=tmp_path) == ["alpha", "beta", "gamma"]


def test_list_snapshots_nonexistent_dir(tmp_path):
    missing = tmp_path / "nope"
    assert list_snapshots(directory=missing) == []


def test_delete_snapshot(tmp_path):
    env = _make_file(("K", "v"))
    save_snapshot(env, "old", directory=tmp_path)
    delete_snapshot("old", directory=tmp_path)
    assert list_snapshots(directory=tmp_path) == []


def test_delete_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        delete_snapshot("nope", directory=tmp_path)


def test_save_overwrites_existing(tmp_path):
    env1 = _make_file(("A", "1"))
    env2 = _make_file(("A", "2"), ("B", "3"))
    save_snapshot(env1, "snap", directory=tmp_path)
    save_snapshot(env2, "snap", directory=tmp_path)
    loaded = load_snapshot("snap", directory=tmp_path)
    assert len(loaded.entries) == 2
    assert loaded.entries[0].value == "2"

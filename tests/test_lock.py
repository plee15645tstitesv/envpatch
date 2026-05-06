"""Tests for envpatch.lock and envpatch.format_lock."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envpatch.lock import (
    LockDrift,
    LockEntry,
    LockFile,
    check_drift,
    generate_lock,
    load_lock,
    save_lock,
)
from envpatch.format_lock import format_drift_report, format_lock_not_found, format_lock_saved
from envpatch.parser import EnvEntry, EnvFile


def _entry(key: str, value: str = "val", is_comment: bool = False) -> EnvEntry:
    return EnvEntry(key=key, value=value, raw=f"{key}={value}", is_comment=is_comment)


def _file(*keys: str) -> EnvFile:
    return EnvFile(entries=[_entry(k) for k in keys])


# --- generate_lock ---

def test_generate_lock_creates_entry_per_key():
    lf = generate_lock(_file("HOST", "PORT"))
    assert lf.keys() == ["HOST", "PORT"]


def test_generate_lock_marks_secret_keys():
    lf = generate_lock(_file("API_SECRET", "HOST"))
    mapping = lf.as_dict()
    assert mapping["API_SECRET"] is True
    assert mapping["HOST"] is False


def test_generate_lock_skips_comments():
    ef = EnvFile(entries=[
        _entry("", is_comment=True),
        _entry("HOST"),
    ])
    lf = generate_lock(ef)
    assert lf.keys() == ["HOST"]


# --- save / load roundtrip ---

def test_save_creates_file(tmp_path):
    lock = generate_lock(_file("HOST", "PORT"))
    path = save_lock(lock, directory=str(tmp_path))
    assert path.exists()


def test_load_roundtrip(tmp_path):
    lock = generate_lock(_file("DB_PASSWORD", "HOST"))
    save_lock(lock, directory=str(tmp_path))
    loaded = load_lock(directory=str(tmp_path))
    assert loaded.keys() == ["DB_PASSWORD", "HOST"]
    assert loaded.as_dict()["DB_PASSWORD"] is True


def test_load_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_lock(directory=str(tmp_path))


def test_save_writes_valid_json(tmp_path):
    lock = generate_lock(_file("HOST"))
    path = save_lock(lock, directory=str(tmp_path))
    data = json.loads(path.read_text())
    assert isinstance(data, list)
    assert data[0]["key"] == "HOST"


# --- check_drift ---

def test_drift_ok_when_identical():
    ef = _file("HOST", "PORT")
    lock = generate_lock(ef)
    drift = check_drift(ef, lock)
    assert drift.ok()


def test_drift_detects_added_key():
    lock = generate_lock(_file("HOST"))
    drift = check_drift(_file("HOST", "NEW_KEY"), lock)
    assert "NEW_KEY" in drift.added
    assert not drift.ok()


def test_drift_detects_removed_key():
    lock = generate_lock(_file("HOST", "OLD_KEY"))
    drift = check_drift(_file("HOST"), lock)
    assert "OLD_KEY" in drift.removed


def test_drift_detects_secret_flag_change():
    lock = LockFile(entries=[LockEntry(key="API_KEY", secret=False)])
    drift = check_drift(_file("API_KEY"), lock)
    assert "API_KEY" in drift.secret_changed


# --- format_lock ---

def test_format_lock_saved_no_colour(tmp_path):
    lock = generate_lock(_file("A", "B"))
    path = tmp_path / ".env.lock"
    msg = format_lock_saved(path, lock, colour=False)
    assert "Lock saved" in msg
    assert "2 keys" in msg


def test_format_drift_ok_no_colour():
    msg = format_drift_report(LockDrift(), colour=False)
    assert "OK" in msg


def test_format_drift_shows_added_key():
    drift = LockDrift(added=["NEW_KEY"])
    msg = format_drift_report(drift, colour=False)
    assert "NEW_KEY" in msg
    assert "new key" in msg


def test_format_drift_with_colour_contains_ansi():
    drift = LockDrift(removed=["OLD_KEY"])
    msg = format_drift_report(drift, colour=True)
    assert "\033[" in msg


def test_format_lock_not_found():
    msg = format_lock_not_found("/some/dir", colour=False)
    assert "Error" in msg
    assert "lock" in msg.lower()

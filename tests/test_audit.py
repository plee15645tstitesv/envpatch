"""Tests for envpatch.audit and envpatch.format_audit."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envpatch.audit import AuditEntry, append_entry, clear_audit_log, load_entries
from envpatch.format_audit import format_audit_entry, format_audit_list


def _entry(**kwargs) -> AuditEntry:
    defaults = dict(
        operation="diff",
        base_file=".env",
        patch_file=".env.staging",
    )
    defaults.update(kwargs)
    return AuditEntry(**defaults)


# ---------------------------------------------------------------------------
# audit.py
# ---------------------------------------------------------------------------

def test_append_creates_file(tmp_path):
    e = _entry()
    path = append_entry(e, directory=str(tmp_path))
    assert path.exists()


def test_append_writes_valid_jsonl(tmp_path):
    append_entry(_entry(keys_added=2), directory=str(tmp_path))
    append_entry(_entry(operation="merge", keys_modified=1), directory=str(tmp_path))
    lines = (tmp_path / ".envpatch_audit.jsonl").read_text().splitlines()
    assert len(lines) == 2
    data = json.loads(lines[0])
    assert data["keys_added"] == 2


def test_load_entries_roundtrip(tmp_path):
    e1 = _entry(keys_added=3, had_conflicts=True)
    e2 = _entry(operation="merge", patch_file=None, note="dry run")
    append_entry(e1, directory=str(tmp_path))
    append_entry(e2, directory=str(tmp_path))
    loaded = load_entries(directory=str(tmp_path))
    assert len(loaded) == 2
    assert loaded[0].keys_added == 3
    assert loaded[0].had_conflicts is True
    assert loaded[1].patch_file is None
    assert loaded[1].note == "dry run"


def test_load_entries_missing_file(tmp_path):
    result = load_entries(directory=str(tmp_path))
    assert result == []


def test_clear_audit_log_existing(tmp_path):
    append_entry(_entry(), directory=str(tmp_path))
    removed = clear_audit_log(directory=str(tmp_path))
    assert removed is True
    assert not (tmp_path / ".envpatch_audit.jsonl").exists()


def test_clear_audit_log_missing(tmp_path):
    removed = clear_audit_log(directory=str(tmp_path))
    assert removed is False


def test_entry_as_dict_keys(tmp_path):
    e = _entry()
    d = e.as_dict()
    for key in ("operation", "base_file", "patch_file", "timestamp",
                "keys_added", "keys_removed", "keys_modified",
                "keys_unchanged", "had_conflicts", "note"):
        assert key in d


# ---------------------------------------------------------------------------
# format_audit.py
# ---------------------------------------------------------------------------

def test_format_list_empty_no_colour():
    result = format_audit_list([], colour=False)
    assert "No audit entries" in result


def test_format_list_contains_entries(tmp_path):
    entries = [_entry(keys_added=1), _entry(operation="merge", keys_removed=2)]
    result = format_audit_list(entries, colour=False)
    assert "diff" in result
    assert "merge" in result


def test_format_list_conflict_marker(tmp_path):
    entries = [_entry(had_conflicts=True)]
    result = format_audit_list(entries, colour=False)
    assert "!" in result


def test_format_list_with_colour_contains_ansi():
    entries = [_entry(keys_added=5)]
    result = format_audit_list(entries, colour=True)
    assert "\033[" in result


def test_format_entry_detail():
    e = _entry(operation="validate", note="ci check", keys_unchanged=10)
    result = format_audit_entry(e, colour=False)
    assert "validate" in result
    assert "ci check" in result
    assert "10" in result


def test_format_entry_no_note_omits_line():
    e = _entry(note="")
    result = format_audit_entry(e, colour=False)
    assert "Note" not in result

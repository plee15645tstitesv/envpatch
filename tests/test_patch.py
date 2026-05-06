"""Tests for envpatch.patch and envpatch.format_patch."""
from __future__ import annotations

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.patch import (
    PatchInstruction,
    PatchOp,
    PatchResult,
    apply_patch,
)
from envpatch.format_patch import (
    format_instruction,
    format_patch_instructions,
    format_patch_result,
)


def _file(*pairs: tuple) -> EnvFile:
    entries = [EnvEntry(key=k, value=v) for k, v in pairs]
    return EnvFile(entries=entries)


# ---------------------------------------------------------------------------
# PatchInstruction validation
# ---------------------------------------------------------------------------

def test_set_requires_value() -> None:
    with pytest.raises(ValueError, match="requires a value"):
        PatchInstruction(op=PatchOp.SET, key="FOO", value=None)


def test_unset_forbids_value() -> None:
    with pytest.raises(ValueError, match="must not carry a value"):
        PatchInstruction(op=PatchOp.UNSET, key="FOO", value="bar")


# ---------------------------------------------------------------------------
# apply_patch — SET
# ---------------------------------------------------------------------------

def test_set_existing_key_updates_value() -> None:
    base = _file(("FOO", "old"), ("BAR", "keep"))
    result = apply_patch(base, [PatchInstruction(PatchOp.SET, "FOO", "new")])
    d = {e.key: e.value for e in result.patched.entries if e.key}
    assert d["FOO"] == "new"
    assert d["BAR"] == "keep"


def test_set_new_key_appends_when_add_missing_true() -> None:
    base = _file(("A", "1"))
    result = apply_patch(base, [PatchInstruction(PatchOp.SET, "B", "2")])
    keys = [e.key for e in result.patched.entries if e.key]
    assert "B" in keys
    assert len(result.applied) == 1
    assert len(result.skipped) == 0


def test_set_new_key_skipped_when_add_missing_false() -> None:
    base = _file(("A", "1"))
    result = apply_patch(
        base,
        [PatchInstruction(PatchOp.SET, "MISSING", "x")],
        add_missing=False,
    )
    keys = [e.key for e in result.patched.entries if e.key]
    assert "MISSING" not in keys
    assert len(result.skipped) == 1
    assert not result.ok


# ---------------------------------------------------------------------------
# apply_patch — UNSET
# ---------------------------------------------------------------------------

def test_unset_existing_key_removes_entry() -> None:
    base = _file(("A", "1"), ("B", "2"))
    result = apply_patch(base, [PatchInstruction(PatchOp.UNSET, "A")])
    keys = [e.key for e in result.patched.entries if e.key]
    assert "A" not in keys
    assert "B" in keys


def test_unset_missing_key_is_skipped() -> None:
    base = _file(("A", "1"))
    result = apply_patch(base, [PatchInstruction(PatchOp.UNSET, "NOPE")])
    assert len(result.skipped) == 1
    assert not result.ok


def test_multiple_instructions_applied_in_order() -> None:
    base = _file(("X", "old"))
    instrs = [
        PatchInstruction(PatchOp.SET, "X", "new"),
        PatchInstruction(PatchOp.SET, "Y", "hello"),
        PatchInstruction(PatchOp.UNSET, "X"),
    ]
    result = apply_patch(base, instrs)
    keys = [e.key for e in result.patched.entries if e.key]
    assert "X" not in keys
    assert "Y" in keys
    assert result.ok


# ---------------------------------------------------------------------------
# format helpers
# ---------------------------------------------------------------------------

def test_format_instruction_set_no_colour() -> None:
    instr = PatchInstruction(PatchOp.SET, "KEY", "val")
    out = format_instruction(instr)
    assert "SET" in out and "KEY=val" in out


def test_format_instruction_unset_no_colour() -> None:
    instr = PatchInstruction(PatchOp.UNSET, "KEY")
    out = format_instruction(instr)
    assert "UNSET" in out and "KEY" in out


def test_format_patch_result_ok_contains_applied() -> None:
    base = _file(("A", "1"))
    result = apply_patch(base, [PatchInstruction(PatchOp.SET, "A", "2")])
    out = format_patch_result(result)
    assert "Applied" in out
    assert "OK" in out


def test_format_patch_result_partial_contains_skipped() -> None:
    base = _file(("A", "1"))
    result = apply_patch(
        base, [PatchInstruction(PatchOp.SET, "Z", "99")], add_missing=False
    )
    out = format_patch_result(result)
    assert "Skipped" in out
    assert "PARTIAL" in out


def test_format_patch_instructions_empty() -> None:
    out = format_patch_instructions([])
    assert "no instructions" in out

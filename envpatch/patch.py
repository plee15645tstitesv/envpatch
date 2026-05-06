"""Apply a structured patch (set/unset operations) to an EnvFile."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from .parser import EnvEntry, EnvFile


class PatchOp(str, Enum):
    SET = "set"
    UNSET = "unset"


@dataclass
class PatchInstruction:
    op: PatchOp
    key: str
    value: Optional[str] = None  # only relevant for SET

    def __post_init__(self) -> None:
        if self.op is PatchOp.SET and self.value is None:
            raise ValueError(f"SET instruction for '{self.key}' requires a value")
        if self.op is PatchOp.UNSET and self.value is not None:
            raise ValueError(f"UNSET instruction for '{self.key}' must not carry a value")


@dataclass
class PatchResult:
    patched: EnvFile
    applied: List[PatchInstruction] = field(default_factory=list)
    skipped: List[PatchInstruction] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.skipped) == 0


def apply_patch(
    base: EnvFile,
    instructions: List[PatchInstruction],
    *,
    add_missing: bool = True,
) -> PatchResult:
    """Return a new EnvFile with *instructions* applied to *base*.

    Parameters
    ----------
    base:
        The original EnvFile to patch.
    instructions:
        Ordered list of SET / UNSET operations.
    add_missing:
        When *True* (default) a SET for an unknown key appends a new entry.
        When *False* the instruction is recorded as skipped instead.
    """
    entries: List[EnvEntry] = list(base.entries)
    index: Dict[str, int] = {
        e.key: i for i, e in enumerate(entries) if e.key is not None
    }

    applied: List[PatchInstruction] = []
    skipped: List[PatchInstruction] = []

    for instr in instructions:
        if instr.op is PatchOp.SET:
            if instr.key in index:
                pos = index[instr.key]
                old = entries[pos]
                entries[pos] = EnvEntry(
                    key=old.key,
                    value=instr.value,
                    comment=old.comment,
                    is_comment=old.is_comment,
                )
                applied.append(instr)
            elif add_missing:
                new_entry = EnvEntry(key=instr.key, value=instr.value)
                index[instr.key] = len(entries)
                entries.append(new_entry)
                applied.append(instr)
            else:
                skipped.append(instr)

        elif instr.op is PatchOp.UNSET:
            if instr.key in index:
                pos = index.pop(instr.key)
                entries.pop(pos)
                # rebuild index positions after removal
                index = {
                    e.key: i for i, e in enumerate(entries) if e.key is not None
                }
                applied.append(instr)
            else:
                skipped.append(instr)

    return PatchResult(
        patched=EnvFile(entries=entries, path=base.path),
        applied=applied,
        skipped=skipped,
    )

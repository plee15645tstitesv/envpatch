"""Human-readable formatting for patch operations and results."""
from __future__ import annotations

from typing import List

from .patch import PatchInstruction, PatchOp, PatchResult


def _c(text: str, code: str, colour: bool) -> str:
    return f"\033[{code}m{text}\033[0m" if colour else text


def format_instruction(instr: PatchInstruction, *, colour: bool = False) -> str:
    """Return a single-line description of one patch instruction."""
    if instr.op is PatchOp.SET:
        op_label = _c("SET", "32", colour)  # green
        return f"{op_label} {instr.key}={instr.value}"
    op_label = _c("UNSET", "31", colour)  # red
    return f"{op_label} {instr.key}"


def format_patch_instructions(
    instructions: List[PatchInstruction], *, colour: bool = False
) -> str:
    """Return a multi-line listing of all instructions."""
    if not instructions:
        return "(no instructions)"
    lines = [format_instruction(i, colour=colour) for i in instructions]
    return "\n".join(lines)


def format_patch_result(result: PatchResult, *, colour: bool = False) -> str:
    """Return a summary of a completed patch operation."""
    lines: List[str] = []

    if result.applied:
        header = _c(f"Applied ({len(result.applied)}):", "32;1", colour)
        lines.append(header)
        for instr in result.applied:
            lines.append(f"  {format_instruction(instr, colour=colour)}")

    if result.skipped:
        header = _c(f"Skipped ({len(result.skipped)}):", "33;1", colour)
        lines.append(header)
        for instr in result.skipped:
            lines.append(f"  {format_instruction(instr, colour=colour)}")

    if not lines:
        return _c("Nothing to apply.", "2", colour)

    status = _c("OK", "32;1", colour) if result.ok else _c("PARTIAL", "33;1", colour)
    lines.append(f"Status: {status}")
    return "\n".join(lines)

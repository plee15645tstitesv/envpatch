"""Format audit log entries for terminal display."""
from __future__ import annotations

from typing import List

from envpatch.audit import AuditEntry

_ANSI_RESET = "\033[0m"
_ANSI_BOLD = "\033[1m"
_ANSI_CYAN = "\033[36m"
_ANSI_YELLOW = "\033[33m"
_ANSI_GREEN = "\033[32m"
_ANSI_RED = "\033[31m"


def _c(text: str, code: str, colour: bool) -> str:
    return f"{code}{text}{_ANSI_RESET}" if colour else text


def format_audit_list(entries: List[AuditEntry], *, colour: bool = False) -> str:
    """Return a human-readable table of audit entries."""
    if not entries:
        return "No audit entries found."

    lines = []
    header = f"{'#':<4} {'Timestamp':<27} {'Operation':<10} {'Base':<24} {'Patch':<24} +A -R ~M"
    lines.append(_c(header, _ANSI_BOLD, colour))
    lines.append("-" * len(header))

    for idx, e in enumerate(entries, 1):
        patch = e.patch_file or "-"
        conflict_marker = _c(" !", _ANSI_RED, colour) if e.had_conflicts else "  "
        row = (
            f"{idx:<4} {e.timestamp:<27} {e.operation:<10} "
            f"{e.base_file:<24} {patch:<24} "
            f"{_c(str(e.keys_added), _ANSI_GREEN, colour):>2} "
            f"{_c(str(e.keys_removed), _ANSI_RED, colour):>2} "
            f"{_c(str(e.keys_modified), _ANSI_YELLOW, colour):>2}"
            f"{conflict_marker}"
        )
        lines.append(row)

    return "\n".join(lines)


def format_audit_entry(entry: AuditEntry, *, colour: bool = False) -> str:
    """Return a single-entry detail block."""
    lines = [
        _c(f"Operation : {entry.operation}", _ANSI_BOLD, colour),
        f"Timestamp : {entry.timestamp}",
        f"Base file : {entry.base_file}",
        f"Patch file: {entry.patch_file or '-'}",
        f"Added     : {entry.keys_added}",
        f"Removed   : {entry.keys_removed}",
        f"Modified  : {entry.keys_modified}",
        f"Unchanged : {entry.keys_unchanged}",
        f"Conflicts : {entry.had_conflicts}",
    ]
    if entry.note:
        lines.append(f"Note      : {entry.note}")
    return "\n".join(lines)

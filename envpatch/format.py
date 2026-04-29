"""Formatting utilities for rendering .env file diffs and merge results."""

from typing import List
from envpatch.diff import DiffEntry, ChangeType
from envpatch.parser import EnvFile
from envpatch.redact import redact_file


ANSI_RED = "\033[31m"
ANSI_GREEN = "\033[32m"
ANSI_YELLOW = "\033[33m"
ANSI_RESET = "\033[0m"
ANSI_DIM = "\033[2m"


def _prefix(change_type: ChangeType) -> str:
    if change_type == ChangeType.ADDED:
        return "+"
    if change_type == ChangeType.REMOVED:
        return "-"
    if change_type == ChangeType.MODIFIED:
        return "~"
    return " "


def format_diff(entries: List[DiffEntry], color: bool = True, redact: bool = True) -> str:
    """Render a list of DiffEntry objects as a human-readable diff string."""
    lines = []
    for entry in entries:
        prefix = _prefix(entry.change_type)
        old_val = entry.display_old(redact=redact)
        new_val = entry.display_new(redact=redact)

        if entry.change_type == ChangeType.UNCHANGED:
            line = f"  {entry.key}={new_val}"
            if color:
                line = f"{ANSI_DIM}{line}{ANSI_RESET}"
        elif entry.change_type == ChangeType.ADDED:
            line = f"{prefix} {entry.key}={new_val}"
            if color:
                line = f"{ANSI_GREEN}{line}{ANSI_RESET}"
        elif entry.change_type == ChangeType.REMOVED:
            line = f"{prefix} {entry.key}={old_val}"
            if color:
                line = f"{ANSI_RED}{line}{ANSI_RESET}"
        else:  # MODIFIED
            old_line = f"- {entry.key}={old_val}"
            new_line = f"+ {entry.key}={new_val}"
            if color:
                old_line = f"{ANSI_RED}{old_line}{ANSI_RESET}"
                new_line = f"{ANSI_GREEN}{new_line}{ANSI_RESET}"
            lines.append(old_line)
            lines.append(new_line)
            continue

        lines.append(line)

    return "\n".join(lines)


def format_env_file(env_file: EnvFile, redact: bool = False) -> str:
    """Render an EnvFile back to .env file format, optionally redacting secrets."""
    source = redact_file(env_file) if redact else env_file
    lines = []
    for entry in source.entries:
        if entry.comment is not None:
            lines.append(entry.comment)
        elif entry.key is None:
            lines.append("")
        else:
            lines.append(f"{entry.key}={entry.value}")
    return "\n".join(lines)

"""Human-readable formatting for lock file operations."""
from __future__ import annotations

from pathlib import Path

from envpatch.lock import LockDrift, LockFile


def _c(text: str, code: str, colour: bool) -> str:
    return f"\033[{code}m{text}\033[0m" if colour else text


def format_lock_saved(path: Path, lock: LockFile, *, colour: bool = False) -> str:
    count = len(lock.entries)
    label = _c("Lock saved", "32", colour)
    return f"{label}: {path} ({count} key{'s' if count != 1 else ''})"


def format_lock_not_found(directory: str, *, colour: bool = False) -> str:
    label = _c("Error", "31", colour)
    return f"{label}: no lock file found in {directory!r}. Run 'envpatch lock generate' first."


def format_drift_report(drift: LockDrift, *, colour: bool = False) -> str:
    if drift.ok():
        ok = _c("OK", "32", colour)
        return f"{ok}: no drift detected."

    lines: list[str] = [_c("Drift detected:", "33", colour)]

    for key in drift.added:
        marker = _c("+", "32", colour)
        lines.append(f"  {marker} {key}  (new key)")  

    for key in drift.removed:
        marker = _c("-", "31", colour)
        lines.append(f"  {marker} {key}  (removed key)")

    for key in drift.secret_changed:
        marker = _c("~", "33", colour)
        lines.append(f"  {marker} {key}  (secret flag changed)")

    summary_parts = []
    if drift.added:
        summary_parts.append(f"{len(drift.added)} added")
    if drift.removed:
        summary_parts.append(f"{len(drift.removed)} removed")
    if drift.secret_changed:
        summary_parts.append(f"{len(drift.secret_changed)} secret-flag changed")

    lines.append("  " + ", ".join(summary_parts))
    return "\n".join(lines)

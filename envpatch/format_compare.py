"""Format a CompareReport for terminal output."""

from __future__ import annotations

from envpatch.compare import CompareReport
from envpatch.format import format_diff

_RESET = "\033[0m"
_BOLD = "\033[1m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RED = "\033[31m"
_CYAN = "\033[36m"


def _c(code: str, text: str, colour: bool) -> str:
    return f"{code}{text}{_RESET}" if colour else text


def format_compare_header(report: CompareReport, *, colour: bool = False) -> str:
    """Return a one-line summary header for the comparison."""
    src = _c(_CYAN, report.source_name, colour)
    tgt = _c(_CYAN, report.target_name, colour)
    label = _c(_BOLD, f"Comparing {src} → {tgt}", colour)
    return label


def format_compare_summary(report: CompareReport, *, colour: bool = False) -> str:
    """Return a compact stats line, e.g. '+2 -1 ~3 =10'."""
    added = _c(_GREEN, f"+{len(report.added)}", colour)
    removed = _c(_RED, f"-{len(report.removed)}", colour)
    modified = _c(_YELLOW, f"~{len(report.modified)}", colour)
    unchanged = f"={len(report.unchanged)}"
    return f"{added}  {removed}  {modified}  {unchanged}"


def format_compare_report(
    report: CompareReport,
    *,
    show_unchanged: bool = False,
    colour: bool = False,
) -> str:
    """Return a full human-readable compare report string."""
    lines: list[str] = [
        format_compare_header(report, colour=colour),
        format_compare_summary(report, colour=colour),
    ]

    all_entries = report.added + report.removed + report.modified
    if show_unchanged:
        all_entries += report.unchanged

    if all_entries:
        lines.append("")
        lines.append(format_diff(all_entries, colour=colour))

    if report.ok:
        msg = _c(_GREEN, "Files are identical.", colour)
        lines.append(msg)

    return "\n".join(lines)

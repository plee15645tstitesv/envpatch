"""Formatting helpers for export command output."""
from __future__ import annotations

from envpatch.export import ExportFormat

_ANSI_GREEN = "\033[32m"
_ANSI_CYAN = "\033[36m"
_ANSI_RESET = "\033[0m"


def _c(text: str, code: str, *, colour: bool) -> str:
    return f"{code}{text}{_ANSI_RESET}" if colour else text


def format_export_header(fmt: ExportFormat, source: str, *, colour: bool = False) -> str:
    """Return a header line describing the export operation."""
    fmt_label = _c(fmt.value.upper(), _ANSI_CYAN, colour=colour)
    src_label = _c(source, _ANSI_GREEN, colour=colour)
    return f"# Exported from {src_label} as {fmt_label}"


def format_export_output(
    content: str,
    fmt: ExportFormat,
    source: str,
    *,
    colour: bool = False,
    show_header: bool = True,
) -> str:
    """Combine an optional header with the exported content."""
    parts: list[str] = []
    if show_header:
        parts.append(format_export_header(fmt, source, colour=colour))
    parts.append(content)
    return "\n".join(parts)


def format_export_formats_list(*, colour: bool = False) -> str:
    """Return a human-readable list of available export formats."""
    names = [_c(f.value, _ANSI_CYAN, colour=colour) for f in ExportFormat]
    return "Available formats: " + ", ".join(names)

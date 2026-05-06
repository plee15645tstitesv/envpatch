"""Formatting helpers for template generation output."""

from __future__ import annotations

from envpatch.template import TemplateResult

_ANSI_GREEN = "\033[32m"
_ANSI_YELLOW = "\033[33m"
_ANSI_RESET = "\033[0m"


def _c(text: str, code: str, *, colour: bool) -> str:
    if not colour:
        return text
    return f"{code}{text}{_ANSI_RESET}"


def format_template_header(source_path: str, *, colour: bool = False) -> str:
    """Return a header line for template generation output."""
    label = _c("template", _ANSI_GREEN, colour=colour)
    return f"[{label}] Generating template from {source_path}"


def format_template_summary(result: TemplateResult, *, colour: bool = False) -> str:
    """Return a one-line summary of what was redacted."""
    total = result.total_count
    redacted = result.redacted_count
    kept = total - redacted

    redacted_str = _c(str(redacted), _ANSI_YELLOW, colour=colour)
    kept_str = _c(str(kept), _ANSI_GREEN, colour=colour)

    return (
        f"  {total} key(s) processed — "
        f"{kept_str} kept, {redacted_str} redacted as secrets"
    )


def format_template_saved(dest_path: str, *, colour: bool = False) -> str:
    """Return a confirmation message after writing the template file."""
    path_str = _c(dest_path, _ANSI_GREEN, colour=colour)
    return f"Template written to {path_str}"


def format_template_output(
    source_path: str,
    dest_path: str,
    result: TemplateResult,
    *,
    colour: bool = False,
) -> str:
    """Combine header, summary and saved lines into a single block."""
    lines = [
        format_template_header(source_path, colour=colour),
        format_template_summary(result, colour=colour),
        format_template_saved(dest_path, colour=colour),
    ]
    return "\n".join(lines)

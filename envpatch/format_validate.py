"""Format helpers for validation and schema results, integrated with
the existing format.py colour/prefix conventions."""

from __future__ import annotations

from envpatch.validate import ValidationResult
from envpatch.schema import SchemaResult

_RESET = "\033[0m"
_RED = "\033[31m"
_YELLOW = "\033[33m"
_GREEN = "\033[32m"
_CYAN = "\033[36m"


def _colour(text: str, code: str, colour: bool) -> str:
    return f"{code}{text}{_RESET}" if colour else text


def format_validation(result: ValidationResult, *, colour: bool = True) -> str:
    """Render a ValidationResult as a human-readable string."""
    if not result.issues:
        return _colour("✔ Validation passed.", _GREEN, colour)

    lines = []
    for issue in result.issues:
        if issue.severity == "error":
            prefix = _colour("✖ ERROR  ", _RED, colour)
        else:
            prefix = _colour("⚠ WARNING", _YELLOW, colour)
        lines.append(
            f"{prefix} line {issue.line_number}: "
            f"{_colour(issue.key, _CYAN, colour)} — {issue.message}"
        )
    return "\n".join(lines)


def format_schema(result: SchemaResult, *, colour: bool = True) -> str:
    """Render a SchemaResult as a human-readable string."""
    if not result.missing and not result.extra:
        return _colour("✔ Schema check passed.", _GREEN, colour)

    lines = []
    for key in result.missing:
        tag = _colour("MISSING", _RED, colour)
        lines.append(f"  [{tag}] {_colour(key, _CYAN, colour)}")
    for key in result.extra:
        tag = _colour("EXTRA", _YELLOW, colour)
        lines.append(f"  [{tag}]   {_colour(key, _CYAN, colour)}")
    return "\n".join(lines)

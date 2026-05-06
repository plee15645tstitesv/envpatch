"""Formatting helpers for validation and schema results."""
from __future__ import annotations

from .schema import SchemaResult
from .validate import ValidationResult


def _colour(text: str, code: str, colour: bool) -> str:
    return f"\033[{code}m{text}\033[0m" if colour else text


def format_validation(result: ValidationResult, *, colour: bool = False) -> str:
    """Return a formatted string for a :class:`ValidationResult`."""
    lines: list[str] = []
    for issue in result.issues:
        if issue.is_error:
            prefix = _colour("ERROR", "31", colour)
        else:
            prefix = _colour("WARN ", "33", colour)
        lines.append(f"  [{prefix}] {issue}")

    if not lines:
        return _colour("Validation passed.", "32", colour)

    header = _colour("Validation issues:", "31" if not result.ok else "33", colour)
    return "\n".join([header] + lines)


def format_schema(result: SchemaResult, *, colour: bool = False) -> str:
    """Return a formatted string for a :class:`SchemaResult`."""
    lines: list[str] = []
    for v in result.violations:
        prefix = _colour("VIOLATION", "31", colour)
        lines.append(f"  [{prefix}] {v}")

    if not lines:
        return _colour("Schema check passed.", "32", colour)

    header = _colour("Schema violations:", "31", colour)
    return "\n".join([header] + lines)

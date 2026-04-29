"""Validation helpers for .env files and diff/merge results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envpatch.parser import EnvFile


@dataclass
class ValidationIssue:
    line_number: int
    key: str
    message: str
    severity: str  # 'error' | 'warning'

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] line {self.line_number}: {self.key!r} — {self.message}"


@dataclass
class ValidationResult:
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(i.severity == "error" for i in self.issues)

    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    def __str__(self) -> str:
        if not self.issues:
            return "Validation passed with no issues."
        return "\n".join(str(i) for i in self.issues)


def validate_file(env_file: EnvFile) -> ValidationResult:
    """Validate an EnvFile for common problems."""
    result = ValidationResult()
    seen_keys: dict[str, int] = {}

    for entry in env_file.entries:
        if entry.comment or entry.blank:
            continue

        lineno = entry.line_number
        key = entry.key or ""

        # Duplicate keys
        if key in seen_keys:
            result.issues.append(
                ValidationIssue(
                    line_number=lineno,
                    key=key,
                    message=f"duplicate key (first seen on line {seen_keys[key]})",
                    severity="error",
                )
            )
        else:
            seen_keys[key] = lineno

        # Empty value warning
        if entry.value == "":
            result.issues.append(
                ValidationIssue(
                    line_number=lineno,
                    key=key,
                    message="empty value",
                    severity="warning",
                )
            )

        # Key contains spaces
        if key and " " in key:
            result.issues.append(
                ValidationIssue(
                    line_number=lineno,
                    key=key,
                    message="key contains whitespace",
                    severity="error",
                )
            )

    return result

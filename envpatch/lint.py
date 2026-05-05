"""Lint .env files for common style and correctness issues."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List

from envpatch.parser import EnvFile, EnvEntry


class LintSeverity(str, Enum):
    WARNING = "warning"
    ERROR = "error"


@dataclass
class LintIssue:
    line: int
    key: str
    message: str
    severity: LintSeverity = LintSeverity.WARNING

    def __str__(self) -> str:
        return f"[{self.severity.value.upper()}] line {self.line}: {self.key!r} — {self.message}"


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(i.severity == LintSeverity.ERROR for i in self.issues)

    @property
    def warnings(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == LintSeverity.WARNING]

    @property
    def errors(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == LintSeverity.ERROR]


def _check_entry(entry: EnvEntry, lineno: int) -> List[LintIssue]:
    issues: List[LintIssue] = []
    if entry.is_comment:
        return issues

    key = entry.key or ""

    # Key should be UPPER_SNAKE_CASE
    if key and key != key.upper():
        issues.append(LintIssue(lineno, key, "key should be uppercase", LintSeverity.WARNING))

    # Key should not start with a digit
    if key and key[0].isdigit():
        issues.append(LintIssue(lineno, key, "key must not start with a digit", LintSeverity.ERROR))

    # Key should not contain spaces
    if key and " " in key:
        issues.append(LintIssue(lineno, key, "key must not contain spaces", LintSeverity.ERROR))

    # Value should not contain unquoted leading/trailing whitespace in raw line
    raw_value = entry.raw_value or ""
    if raw_value != raw_value.strip() and not (
        raw_value.startswith('"') or raw_value.startswith("'")
    ):
        issues.append(
            LintIssue(lineno, key, "value has unquoted leading/trailing whitespace", LintSeverity.WARNING)
        )

    # Empty value is a warning
    if entry.value == "" and not entry.is_comment:
        issues.append(LintIssue(lineno, key, "value is empty", LintSeverity.WARNING))

    return issues


def lint(env_file: EnvFile) -> LintResult:
    """Run all lint checks against *env_file* and return a LintResult."""
    result = LintResult()
    seen_keys: dict[str, int] = {}

    for lineno, entry in enumerate(env_file.entries, start=1):
        if entry.is_comment:
            continue

        key = entry.key or ""

        # Duplicate key detection
        if key in seen_keys:
            result.issues.append(
                LintIssue(lineno, key, f"duplicate key (first seen at line {seen_keys[key]})", LintSeverity.ERROR)
            )
        else:
            seen_keys[key] = lineno

        result.issues.extend(_check_entry(entry, lineno))

    return result

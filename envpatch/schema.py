"""Optional schema / template validation: check that an env file satisfies
a reference template (e.g. .env.example)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Set

from envpatch.parser import EnvFile, keys as env_keys


@dataclass
class SchemaViolation:
    key: str
    message: str

    def __str__(self) -> str:
        return f"{self.key!r}: {self.message}"


@dataclass
class SchemaResult:
    missing: List[str] = field(default_factory=list)
    extra: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.missing

    @property
    def violations(self) -> List[SchemaViolation]:
        v: List[SchemaViolation] = []
        for k in self.missing:
            v.append(SchemaViolation(k, "required key missing from env file"))
        for k in self.extra:
            v.append(SchemaViolation(k, "key not present in template"))
        return v

    def __str__(self) -> str:
        if not self.missing and not self.extra:
            return "Schema check passed."
        lines = []
        for k in self.missing:
            lines.append(f"[MISSING] {k!r}")
        for k in self.extra:
            lines.append(f"[EXTRA]   {k!r}")
        return "\n".join(lines)


def check_schema(
    template: EnvFile,
    target: EnvFile,
    allow_extra: bool = True,
) -> SchemaResult:
    """Compare *target* against *template*.

    Args:
        template: The reference .env.example file.
        target:   The actual .env file being checked.
        allow_extra: When False, keys in *target* not in *template* are
                     reported as extra.
    """
    template_keys: Set[str] = set(env_keys(template))
    target_keys: Set[str] = set(env_keys(target))

    missing = sorted(template_keys - target_keys)
    extra = sorted(target_keys - template_keys) if not allow_extra else []

    return SchemaResult(missing=missing, extra=extra)

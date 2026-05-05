"""Variable interpolation for .env files.

Supports ${VAR} and $VAR syntax, resolving references within the same
EnvFile or against an optional external context dictionary.
"""

from __future__ import annotations

import re
from typing import Optional

from envpatch.parser import EnvFile, EnvEntry

_BRACE_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
_BARE_RE = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)")


class InterpolationError(Exception):
    """Raised when a variable reference cannot be resolved."""

    def __init__(self, key: str, ref: str) -> None:
        self.key = key
        self.ref = ref
        super().__init__(f"Key '{key}': unresolved reference '${ref}'")


def _resolve_value(
    value: str,
    context: dict[str, str],
    strict: bool,
    key: str,
) -> str:
    """Replace all ${VAR} and $VAR placeholders in *value*."""

    def _replace(match: re.Match) -> str:  # type: ignore[type-arg]
        ref = match.group(1)
        if ref in context:
            return context[ref]
        if strict:
            raise InterpolationError(key, ref)
        return match.group(0)  # leave unresolved placeholder as-is

    result = _BRACE_RE.sub(_replace, value)
    result = _BARE_RE.sub(_replace, result)
    return result


def interpolate(
    env_file: EnvFile,
    extra: Optional[dict[str, str]] = None,
    strict: bool = False,
) -> EnvFile:
    """Return a new EnvFile with variable references expanded.

    Resolution order:
    1. Keys already defined earlier in the same file (in order).
    2. Keys provided in *extra* (e.g. OS environment).

    If *strict* is True, raise InterpolationError for unresolved references.
    """
    context: dict[str, str] = dict(extra or {})
    new_entries: list[EnvEntry] = []

    for entry in env_file.entries:
        if entry.is_comment or entry.key is None or entry.value is None:
            new_entries.append(entry)
            continue

        resolved = _resolve_value(entry.value, context, strict, entry.key)
        context[entry.key] = resolved

        new_entries.append(
            EnvEntry(
                key=entry.key,
                value=resolved,
                is_comment=entry.is_comment,
                raw=entry.raw,
            )
        )

    return EnvFile(entries=new_entries)

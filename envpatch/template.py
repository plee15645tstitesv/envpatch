"""Template generation: produce a .env.example from an EnvFile, redacting secret values."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envpatch.parser import EnvEntry, EnvFile, is_secret

_PLACEHOLDER = "<YOUR_VALUE_HERE>"
_SECRET_PLACEHOLDER = "<SECRET>"


@dataclass
class TemplateResult:
    """Outcome of rendering a template from an EnvFile."""

    entries: List[EnvEntry] = field(default_factory=list)
    redacted_count: int = 0
    total_count: int = 0

    @property
    def ok(self) -> bool:  # noqa: D401
        return len(self.entries) > 0 or self.total_count == 0


def generate_template(
    env_file: EnvFile,
    *,
    redact_secrets: bool = True,
    blank_non_secrets: bool = False,
) -> TemplateResult:
    """Return a TemplateResult whose entries are safe for committing.

    Parameters
    ----------
    env_file:
        The source :class:`EnvFile` to template.
    redact_secrets:
        When *True* (default), secret keys receive ``<SECRET>`` as their value.
    blank_non_secrets:
        When *True*, non-secret values are replaced with ``<YOUR_VALUE_HERE>``.
        When *False* (default), non-secret values are kept as-is.
    """
    out_entries: List[EnvEntry] = []
    redacted = 0
    total = 0

    for entry in env_file.entries:
        if entry.is_comment or entry.key is None:
            out_entries.append(entry)
            continue

        total += 1
        secret = is_secret(entry.key)

        if secret and redact_secrets:
            new_entry = EnvEntry(
                key=entry.key,
                value=_SECRET_PLACEHOLDER,
                is_comment=False,
                raw=f"{entry.key}={_SECRET_PLACEHOLDER}",
            )
            redacted += 1
        elif blank_non_secrets and not secret:
            new_entry = EnvEntry(
                key=entry.key,
                value=_PLACEHOLDER,
                is_comment=False,
                raw=f"{entry.key}={_PLACEHOLDER}",
            )
        else:
            new_entry = entry

        out_entries.append(new_entry)

    return TemplateResult(
        entries=out_entries,
        redacted_count=redacted,
        total_count=total,
    )


def render_template(result: TemplateResult) -> str:
    """Serialise a :class:`TemplateResult` back to .env text."""
    return "\n".join(e.raw for e in result.entries)

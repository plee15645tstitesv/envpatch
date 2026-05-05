"""Utilities for redacting secret values in .env files before display or export."""

from typing import Optional
from envpatch.parser import EnvFile, EnvEntry, is_secret

REDACTED_PLACEHOLDER = "***REDACTED***"


def redact_entry(entry: EnvEntry, placeholder: str = REDACTED_PLACEHOLDER) -> EnvEntry:
    """Return a copy of the entry with its value replaced if it is a secret."""
    if entry.is_comment or entry.is_blank:
        return entry
    if is_secret(entry.key):
        return EnvEntry(
            key=entry.key,
            value=placeholder,
            raw_line=f"{entry.key}={placeholder}",
            is_comment=False,
            is_blank=False,
        )
    return entry


def redact_file(env_file: EnvFile, placeholder: str = REDACTED_PLACEHOLDER) -> EnvFile:
    """Return a new EnvFile with all secret values redacted."""
    redacted_entries = [redact_entry(e, placeholder) for e in env_file.entries]
    return EnvFile(entries=redacted_entries)


def redact_value(key: str, value: Optional[str], placeholder: str = REDACTED_PLACEHOLDER) -> str:
    """Redact a single value by key name if it matches secret heuristics."""
    if value is None:
        return ""
    if is_secret(key):
        return placeholder
    return value


def redact_dict(
    data: dict, placeholder: str = REDACTED_PLACEHOLDER
) -> dict:
    """Return a copy of a key/value dict with secret values redacted.

    Useful for redacting os.environ-style mappings or parsed env dicts
    before logging or passing to external systems.
    """
    return {key: redact_value(key, value, placeholder) for key, value in data.items()}


def safe_display(env_file: EnvFile, placeholder: str = REDACTED_PLACEHOLDER) -> str:
    """Render an EnvFile as a string with secrets redacted, safe for logging/display."""
    lines = []
    for entry in env_file.entries:
        if entry.is_blank or entry.is_comment:
            lines.append(entry.raw_line)
        else:
            safe_val = redact_value(entry.key, entry.value, placeholder)
            lines.append(f"{entry.key}={safe_val}")
    return "\n".join(lines)

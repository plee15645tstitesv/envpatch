"""Export .env files to various formats (shell, JSON, Docker)."""
from __future__ import annotations

import json
import shlex
from enum import Enum
from typing import Optional

from envpatch.parser import EnvFile
from envpatch.redact import redact_file


class ExportFormat(str, Enum):
    SHELL = "shell"
    JSON = "json"
    DOCKER = "docker"


def export_shell(env: EnvFile, *, redact: bool = False) -> str:
    """Export as shell export statements: export KEY=value"""
    if redact:
        env = redact_file(env)
    lines: list[str] = []
    for entry in env.entries:
        if entry.is_comment or entry.key is None:
            continue
        safe_val = shlex.quote(entry.value if entry.value is not None else "")
        lines.append(f"export {entry.key}={safe_val}")
    return "\n".join(lines)


def export_json(env: EnvFile, *, redact: bool = False) -> str:
    """Export as a JSON object mapping keys to values."""
    if redact:
        env = redact_file(env)
    data: dict[str, Optional[str]] = {}
    for entry in env.entries:
        if entry.is_comment or entry.key is None:
            continue
        data[entry.key] = entry.value
    return json.dumps(data, indent=2)


def export_docker(env: EnvFile, *, redact: bool = False) -> str:
    """Export as Docker --env-file compatible format (KEY=value, no quotes)."""
    if redact:
        env = redact_file(env)
    lines: list[str] = []
    for entry in env.entries:
        if entry.is_comment or entry.key is None:
            continue
        val = entry.value if entry.value is not None else ""
        lines.append(f"{entry.key}={val}")
    return "\n".join(lines)


def export_env(env: EnvFile, fmt: ExportFormat, *, redact: bool = False) -> str:
    """Dispatch export to the requested format."""
    if fmt == ExportFormat.SHELL:
        return export_shell(env, redact=redact)
    if fmt == ExportFormat.JSON:
        return export_json(env, redact=redact)
    if fmt == ExportFormat.DOCKER:
        return export_docker(env, redact=redact)
    raise ValueError(f"Unknown export format: {fmt}")

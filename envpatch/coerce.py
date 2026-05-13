"""Coerce .env values to typed Python objects."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from envpatch.parser import EnvFile, EnvEntry


@dataclass
class CoerceResult:
    env_name: str
    coerced: Dict[str, Any] = field(default_factory=dict)
    skipped: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def ok(self) -> bool:
        return len(self.errors) == 0


def _coerce_value(value: str) -> Any:
    """Attempt to coerce a string value to bool, int, float, list, or str."""
    if value.lower() in ("true", "yes", "1"):
        return True
    if value.lower() in ("false", "no", "0"):
        return False
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    # Comma-separated list detection
    if "," in value:
        parts = [p.strip() for p in value.split(",")]
        if all(parts):
            return parts
    return value


def coerce(
    env_file: EnvFile,
    keys: Optional[List[str]] = None,
    skip_secrets: bool = False,
) -> CoerceResult:
    """Coerce values in *env_file* to native Python types.

    Args:
        env_file:     The parsed .env file to process.
        keys:         Optional allowlist of keys to coerce; all keys if None.
        skip_secrets: When True, secret-flagged entries are added to skipped
                      rather than coerced.

    Returns:
        A :class:`CoerceResult` with the coerced mapping and any issues.
    """
    result = CoerceResult(env_name=env_file.env_name)

    for entry in env_file.entries:
        if entry.comment:
            continue
        if keys is not None and entry.key not in keys:
            continue
        if skip_secrets and entry.secret:
            result.skipped.append(entry.key)
            continue
        if entry.value is None:
            result.skipped.append(entry.key)
            continue
        try:
            result.coerced[entry.key] = _coerce_value(entry.value)
        except Exception as exc:  # pragma: no cover
            result.errors.append(f"{entry.key}: {exc}")

    return result

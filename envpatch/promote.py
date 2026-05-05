"""Promote an .env file from one environment to another, applying redaction and merge rules."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .parser import EnvFile
from .redact import redact_file
from .merge import ConflictStrategy, merge
from .audit import AuditEntry, append_entry


@dataclass
class PromoteResult:
    source_env: str
    target_env: str
    merged: EnvFile
    skipped_secrets: list[str] = field(default_factory=list)
    conflicts_resolved: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return True  # promote always produces a result; callers inspect details


def promote(
    source: EnvFile,
    target: EnvFile,
    source_env: str,
    target_env: str,
    *,
    carry_secrets: bool = False,
    conflict_strategy: ConflictStrategy = ConflictStrategy.USE_PATCH,
    add_missing: bool = True,
    audit_dir: Optional[str] = None,
) -> PromoteResult:
    """Promote *source* onto *target*, optionally stripping secrets.

    Parameters
    ----------
    source:
        The environment being promoted from (e.g. staging).
    target:
        The environment being promoted into (e.g. production).
    carry_secrets:
        When False (default) secret-flagged keys in *source* are stripped
        before the merge so they never overwrite production secrets.
    conflict_strategy:
        How to resolve keys present in both files.
    add_missing:
        Whether keys present only in *source* are added to *target*.
    audit_dir:
        If provided, an audit entry is appended to this directory.
    """
    patch = redact_file(source) if not carry_secrets else source

    skipped: list[str] = []
    if not carry_secrets:
        for entry in source.entries:
            if entry.is_secret and entry.key and entry.key not in [
                e.key for e in patch.entries if e.key
            ]:
                skipped.append(entry.key)

    # Track which keys exist in both files (potential conflicts)
    source_keys = {e.key for e in patch.entries if e.key}
    target_keys = {e.key for e in target.entries if e.key}
    conflicts_resolved = sorted(source_keys & target_keys)

    merged = merge(
        base=target,
        patch=patch,
        conflict_strategy=conflict_strategy,
        add_missing=add_missing,
    )

    result = PromoteResult(
        source_env=source_env,
        target_env=target_env,
        merged=merged,
        skipped_secrets=skipped,
        conflicts_resolved=conflicts_resolved,
    )

    if audit_dir is not None:
        entry = AuditEntry(
            action="promote",
            detail=(
                f"{source_env} -> {target_env} | "
                f"conflicts={len(conflicts_resolved)} "
                f"skipped_secrets={len(skipped)}"
            ),
        )
        append_entry(audit_dir, entry)

    return result

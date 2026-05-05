"""Tests for envpatch.promote."""

from __future__ import annotations

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.merge import ConflictStrategy
from envpatch.promote import promote, PromoteResult


def _entry(key: str, value: str, *, secret: bool = False, comment: bool = False) -> EnvEntry:
    return EnvEntry(key=key, value=value, is_secret=secret, is_comment=comment, raw=f"{key}={value}")


def _file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


# ---------------------------------------------------------------------------
# Basic promotion
# ---------------------------------------------------------------------------

def test_promote_returns_result():
    source = _file(_entry("APP_NAME", "myapp"))
    target = _file(_entry("APP_NAME", "oldapp"))
    result = promote(source, target, "staging", "production")
    assert isinstance(result, PromoteResult)
    assert result.ok


def test_promote_source_and_target_env_names_stored():
    source = _file(_entry("X", "1"))
    target = _file(_entry("X", "2"))
    result = promote(source, target, "dev", "prod")
    assert result.source_env == "dev"
    assert result.target_env == "prod"


def test_promote_non_secret_key_overwrites_target_by_default():
    source = _file(_entry("FEATURE_FLAG", "true"))
    target = _file(_entry("FEATURE_FLAG", "false"))
    result = promote(source, target, "staging", "production")
    merged_dict = {e.key: e.value for e in result.merged.entries if e.key}
    assert merged_dict["FEATURE_FLAG"] == "true"


def test_promote_secret_stripped_by_default():
    source = _file(
        _entry("API_KEY", "staging-secret", secret=True),
        _entry("APP_ENV", "staging"),
    )
    target = _file(
        _entry("API_KEY", "prod-secret", secret=True),
        _entry("APP_ENV", "production"),
    )
    result = promote(source, target, "staging", "production", carry_secrets=False)
    merged_dict = {e.key: e.value for e in result.merged.entries if e.key}
    # Secret from source must NOT overwrite target
    assert merged_dict.get("API_KEY") == "prod-secret"


def test_promote_carry_secrets_true_overwrites_secret():
    source = _file(_entry("DB_PASS", "new-pass", secret=True))
    target = _file(_entry("DB_PASS", "old-pass", secret=True))
    result = promote(source, target, "staging", "production", carry_secrets=True)
    merged_dict = {e.key: e.value for e in result.merged.entries if e.key}
    assert merged_dict["DB_PASS"] == "new-pass"


def test_promote_add_missing_false_does_not_add_new_keys():
    source = _file(_entry("NEW_KEY", "hello"))
    target = _file(_entry("EXISTING", "world"))
    result = promote(source, target, "staging", "production", add_missing=False)
    keys = {e.key for e in result.merged.entries if e.key}
    assert "NEW_KEY" not in keys
    assert "EXISTING" in keys


def test_promote_conflicts_resolved_lists_shared_keys():
    source = _file(_entry("SHARED", "a"), _entry("ONLY_SOURCE", "b"))
    target = _file(_entry("SHARED", "x"), _entry("ONLY_TARGET", "y"))
    result = promote(source, target, "staging", "production")
    assert "SHARED" in result.conflicts_resolved
    assert "ONLY_SOURCE" not in result.conflicts_resolved


def test_promote_base_wins_conflict_strategy():
    source = _file(_entry("KEY", "source-val"))
    target = _file(_entry("KEY", "target-val"))
    result = promote(
        source, target, "staging", "production",
        conflict_strategy=ConflictStrategy.USE_BASE,
    )
    merged_dict = {e.key: e.value for e in result.merged.entries if e.key}
    assert merged_dict["KEY"] == "target-val"


def test_promote_audit_appended(tmp_path):
    from envpatch.audit import load_entries
    source = _file(_entry("X", "1"))
    target = _file(_entry("X", "2"))
    promote(source, target, "staging", "production", audit_dir=str(tmp_path))
    entries = load_entries(str(tmp_path))
    assert len(entries) == 1
    assert entries[0].action == "promote"

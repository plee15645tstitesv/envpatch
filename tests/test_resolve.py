"""Tests for envpatch.resolve."""
import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.resolve import resolve, ResolveResult


def _entry(key: str, value: str = "val", secret: bool = False, comment: bool = False) -> EnvEntry:
    return EnvEntry(key=key, value=value, secret=secret, comment=comment, raw=f"{key}={value}")


def _file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


def test_resolve_returns_result():
    result = resolve(_file(_entry("A")), _file(), source_env="prod", target_env="dev")
    assert isinstance(result, ResolveResult)
    assert result.source_env == "prod"
    assert result.target_env == "dev"


def test_resolve_fills_missing_key():
    source = _file(_entry("A", "alpha"))
    target = _file()
    result = resolve(source, target)
    assert result.total_filled() == 1
    assert result.filled[0].key == "A"


def test_resolve_skips_existing_key_by_default():
    source = _file(_entry("A", "from_source"))
    target = _file(_entry("A", "from_target"))
    result = resolve(source, target)
    assert result.total_filled() == 0
    assert result.total_skipped() == 1
    assert "A" in result.skipped


def test_resolve_overwrites_existing_when_flag_set():
    source = _file(_entry("A", "new_value"))
    target = _file(_entry("A", "old_value"))
    result = resolve(source, target, overwrite_existing=True)
    assert result.total_filled() == 1
    # Confirm output carries new value
    out_map = {e.key: e.value for e in result.output.entries if e.key}
    assert out_map["A"] == "new_value"


def test_resolve_redacts_secret_by_default():
    source = _file(_entry("SECRET_KEY", "supersecret", secret=True))
    target = _file()
    result = resolve(source, target)
    assert result.total_filled() == 1
    filled_entry = result.filled[0]
    assert filled_entry.value != "supersecret"


def test_resolve_keeps_secret_when_redact_disabled():
    source = _file(_entry("SECRET_KEY", "supersecret", secret=True))
    target = _file()
    result = resolve(source, target, redact_secrets=False)
    assert result.filled[0].value == "supersecret"


def test_resolve_output_contains_original_target_entries():
    source = _file(_entry("NEW", "n"))
    target = _file(_entry("EXISTING", "e"))
    result = resolve(source, target)
    out_keys = {e.key for e in result.output.entries if e.key}
    assert "EXISTING" in out_keys
    assert "NEW" in out_keys


def test_resolve_ok_is_always_true():
    result = resolve(_file(), _file())
    assert result.ok() is True


def test_resolve_multiple_missing_keys():
    source = _file(_entry("A"), _entry("B"), _entry("C"))
    target = _file(_entry("B", "already"))
    result = resolve(source, target)
    filled_keys = {e.key for e in result.filled}
    assert "A" in filled_keys
    assert "C" in filled_keys
    assert "B" not in filled_keys
    assert result.total_skipped() == 1

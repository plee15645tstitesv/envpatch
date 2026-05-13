"""Tests for envpatch.coerce."""
from __future__ import annotations

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.coerce import CoerceResult, _coerce_value, coerce


def _entry(key: str, value: str, secret: bool = False) -> EnvEntry:
    return EnvEntry(key=key, value=value, raw=f"{key}={value}", comment=False, secret=secret)


def _comment() -> EnvEntry:
    return EnvEntry(key="", value=None, raw="# comment", comment=True, secret=False)


def _file(*entries: EnvEntry, env_name: str = "test") -> EnvFile:
    return EnvFile(env_name=env_name, entries=list(entries))


# --- _coerce_value unit tests ---

@pytest.mark.parametrize("val", ["true", "True", "TRUE", "yes", "Yes", "1"])
def test_coerce_truthy_values(val):
    assert _coerce_value(val) is True


@pytest.mark.parametrize("val", ["false", "False", "FALSE", "no", "No", "0"])
def test_coerce_falsy_values(val):
    assert _coerce_value(val) is False


def test_coerce_integer():
    assert _coerce_value("42") == 42
    assert isinstance(_coerce_value("42"), int)


def test_coerce_float():
    assert _coerce_value("3.14") == pytest.approx(3.14)
    assert isinstance(_coerce_value("3.14"), float)


def test_coerce_comma_list():
    result = _coerce_value("a,b,c")
    assert result == ["a", "b", "c"]


def test_coerce_string_fallback():
    assert _coerce_value("hello") == "hello"


# --- coerce() integration tests ---

def test_coerce_returns_result():
    f = _file(_entry("PORT", "8080"))
    result = coerce(f)
    assert isinstance(result, CoerceResult)


def test_coerce_ok_when_no_errors():
    f = _file(_entry("DEBUG", "true"))
    result = coerce(f)
    assert result.ok()


def test_coerce_bool_entry():
    f = _file(_entry("ENABLED", "true"))
    result = coerce(f)
    assert result.coerced["ENABLED"] is True


def test_coerce_int_entry():
    f = _file(_entry("WORKERS", "4"))
    result = coerce(f)
    assert result.coerced["WORKERS"] == 4


def test_coerce_list_entry():
    f = _file(_entry("ALLOWED_HOSTS", "localhost,127.0.0.1,example.com"))
    result = coerce(f)
    assert result.coerced["ALLOWED_HOSTS"] == ["localhost", "127.0.0.1", "example.com"]


def test_coerce_skips_comments():
    f = _file(_comment(), _entry("X", "1"))
    result = coerce(f)
    assert "" not in result.coerced
    assert "X" in result.coerced


def test_coerce_keys_allowlist():
    f = _file(_entry("A", "1"), _entry("B", "2"), _entry("C", "3"))
    result = coerce(f, keys=["A", "C"])
    assert set(result.coerced.keys()) == {"A", "C"}


def test_coerce_skip_secrets():
    f = _file(
        _entry("API_KEY", "secret123", secret=True),
        _entry("PORT", "9000", secret=False),
    )
    result = coerce(f, skip_secrets=True)
    assert "API_KEY" not in result.coerced
    assert "API_KEY" in result.skipped
    assert result.coerced["PORT"] == 9000


def test_coerce_none_value_skipped():
    entry = EnvEntry(key="EMPTY", value=None, raw="EMPTY", comment=False, secret=False)
    f = _file(entry)
    result = coerce(f)
    assert "EMPTY" not in result.coerced
    assert "EMPTY" in result.skipped


def test_coerce_env_name_stored():
    f = _file(env_name="production")
    result = coerce(f)
    assert result.env_name == "production"

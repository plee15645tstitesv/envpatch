"""Tests for envpatch.redact module."""

import pytest
from envpatch.parser import EnvFile, EnvEntry
from envpatch.redact import (
    redact_entry,
    redact_file,
    redact_value,
    safe_display,
    REDACTED_PLACEHOLDER,
)


def _make_entry(key: str, value: str) -> EnvEntry:
    return EnvEntry(
        key=key,
        value=value,
        raw_line=f"{key}={value}",
        is_comment=False,
        is_blank=False,
    )


def _make_file(pairs: list) -> EnvFile:
    entries = [_make_entry(k, v) for k, v in pairs]
    return EnvFile(entries=entries)


def test_redact_entry_secret_key():
    entry = _make_entry("SECRET_TOKEN", "abc123")
    result = redact_entry(entry)
    assert result.value == REDACTED_PLACEHOLDER
    assert result.key == "SECRET_TOKEN"


def test_redact_entry_non_secret_key():
    entry = _make_entry("APP_NAME", "myapp")
    result = redact_entry(entry)
    assert result.value == "myapp"


def test_redact_entry_comment_unchanged():
    entry = EnvEntry(key="", value="", raw_line="# comment", is_comment=True, is_blank=False)
    result = redact_entry(entry)
    assert result.raw_line == "# comment"


def test_redact_entry_blank_unchanged():
    entry = EnvEntry(key="", value="", raw_line="", is_comment=False, is_blank=True)
    result = redact_entry(entry)
    assert result.is_blank is True


def test_redact_file_redacts_secrets():
    env = _make_file([("APP_NAME", "myapp"), ("DB_PASSWORD", "s3cr3t"), ("PORT", "8080")])
    redacted = redact_file(env)
    values = {e.key: e.value for e in redacted.entries if not e.is_blank and not e.is_comment}
    assert values["APP_NAME"] == "myapp"
    assert values["DB_PASSWORD"] == REDACTED_PLACEHOLDER
    assert values["PORT"] == "8080"


def test_redact_value_secret():
    assert redact_value("API_KEY", "topsecret") == REDACTED_PLACEHOLDER


def test_redact_value_non_secret():
    assert redact_value("APP_ENV", "production") == "production"


def test_redact_value_none():
    assert redact_value("API_KEY", None) == ""


def test_safe_display_redacts_and_preserves_comments():
    comment = EnvEntry(key="", value="", raw_line="# env config", is_comment=True, is_blank=False)
    blank = EnvEntry(key="", value="", raw_line="", is_comment=False, is_blank=True)
    normal = _make_entry("APP_NAME", "myapp")
    secret = _make_entry("SECRET_KEY", "hunter2")
    env = EnvFile(entries=[comment, blank, normal, secret])
    output = safe_display(env)
    assert "# env config" in output
    assert "APP_NAME=myapp" in output
    assert "SECRET_KEY=" + REDACTED_PLACEHOLDER in output
    assert "hunter2" not in output


def test_redact_custom_placeholder():
    entry = _make_entry("DB_PASSWORD", "secret")
    result = redact_entry(entry, placeholder="[hidden]")
    assert result.value == "[hidden]"

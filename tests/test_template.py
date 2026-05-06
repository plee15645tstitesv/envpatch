"""Tests for envpatch.template and envpatch.format_template."""

from __future__ import annotations

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.template import (
    TemplateResult,
    generate_template,
    render_template,
    _SECRET_PLACEHOLDER,
    _PLACEHOLDER,
)
from envpatch.format_template import (
    format_template_header,
    format_template_summary,
    format_template_saved,
    format_template_output,
)


def _entry(key: str, value: str, is_comment: bool = False) -> EnvEntry:
    raw = f"# {value}" if is_comment else f"{key}={value}"
    return EnvEntry(key=None if is_comment else key, value=value, is_comment=is_comment, raw=raw)


def _file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


# ---------------------------------------------------------------------------
# generate_template
# ---------------------------------------------------------------------------

def test_secret_key_is_redacted_by_default():
    f = _file(_entry("SECRET_KEY", "abc123"))
    result = generate_template(f)
    assert result.redacted_count == 1
    assert result.entries[0].value == _SECRET_PLACEHOLDER


def test_non_secret_key_kept_by_default():
    f = _file(_entry("APP_NAME", "myapp"))
    result = generate_template(f)
    assert result.redacted_count == 0
    assert result.entries[0].value == "myapp"


def test_blank_non_secrets_flag():
    f = _file(_entry("APP_NAME", "myapp"))
    result = generate_template(f, blank_non_secrets=True)
    assert result.entries[0].value == _PLACEHOLDER


def test_redact_secrets_false_keeps_secret_value():
    f = _file(_entry("DB_PASSWORD", "hunter2"))
    result = generate_template(f, redact_secrets=False)
    assert result.redacted_count == 0
    assert result.entries[0].value == "hunter2"


def test_comments_pass_through_unchanged():
    comment = _entry("", "a comment", is_comment=True)
    f = _file(comment)
    result = generate_template(f)
    assert result.total_count == 0
    assert result.entries[0].is_comment is True


def test_total_count_excludes_comments():
    f = _file(
        _entry("", "comment", is_comment=True),
        _entry("APP_ENV", "production"),
        _entry("API_SECRET", "s3cr3t"),
    )
    result = generate_template(f)
    assert result.total_count == 2


def test_result_ok_non_empty():
    f = _file(_entry("X", "1"))
    result = generate_template(f)
    assert result.ok is True


def test_result_ok_empty_file():
    result = generate_template(_file())
    assert result.ok is True


# ---------------------------------------------------------------------------
# render_template
# ---------------------------------------------------------------------------

def test_render_template_produces_env_text():
    f = _file(_entry("APP_NAME", "myapp"), _entry("DB_PASSWORD", "secret"))
    result = generate_template(f)
    rendered = render_template(result)
    assert "APP_NAME=myapp" in rendered
    assert _SECRET_PLACEHOLDER in rendered


# ---------------------------------------------------------------------------
# format_template helpers
# ---------------------------------------------------------------------------

def test_format_header_contains_path():
    out = format_template_header("/app/.env")
    assert "/app/.env" in out


def test_format_summary_counts():
    result = TemplateResult(entries=[], redacted_count=3, total_count=5)
    out = format_template_summary(result)
    assert "3" in out
    assert "2" in out  # kept = 5 - 3


def test_format_saved_contains_dest():
    out = format_template_saved("/app/.env.example")
    assert "/app/.env.example" in out


def test_format_output_with_colour_contains_ansi():
    result = TemplateResult(entries=[], redacted_count=1, total_count=2)
    out = format_template_output("/app/.env", "/app/.env.example", result, colour=True)
    assert "\033[" in out


def test_format_output_no_colour_no_ansi():
    result = TemplateResult(entries=[], redacted_count=0, total_count=1)
    out = format_template_output("/app/.env", "/app/.env.example", result, colour=False)
    assert "\033[" not in out

"""Tests for envpatch.parser — .env file parsing."""

import textwrap
from pathlib import Path

import pytest

from envpatch.parser import EnvEntry, parse_env_file, parse_env_string


SAMPLE_ENV = textwrap.dedent("""\
    # Database config
    DB_HOST=localhost
    DB_PORT=5432
    DB_PASSWORD="super secret"

    # App
    APP_NAME='My App'
    API_KEY=abc123
    DEBUG=true
""")


def test_parse_basic_entries():
    env = parse_env_string(SAMPLE_ENV)
    keys = [e.key for e in env.entries]
    assert "DB_HOST" in keys
    assert "DB_PORT" in keys
    assert "APP_NAME" in keys


def test_comments_and_blanks_ignored():
    env = parse_env_string(SAMPLE_ENV)
    for entry in env.entries:
        assert not entry.key.startswith("#")
    assert len(env.entries) == 6


def test_double_quote_stripping():
    env = parse_env_string(SAMPLE_ENV)
    mapping = env.as_dict
    assert mapping["DB_PASSWORD"] == "super secret"


def test_single_quote_stripping():
    env = parse_env_string(SAMPLE_ENV)
    assert env.as_dict["APP_NAME"] == "My App"


def test_unquoted_value():
    env = parse_env_string(SAMPLE_ENV)
    assert env.as_dict["DB_HOST"] == "localhost"


def test_as_dict_returns_all_keys():
    env = parse_env_string(SAMPLE_ENV)
    d = env.as_dict
    assert isinstance(d, dict)
    assert d["DEBUG"] == "true"


def test_is_secret_detection():
    entry_secret = EnvEntry(key="DB_PASSWORD", value="x", line_number=1, raw="DB_PASSWORD=x")
    entry_plain = EnvEntry(key="DB_HOST", value="localhost", line_number=2, raw="DB_HOST=localhost")
    assert entry_secret.is_secret() is True
    assert entry_plain.is_secret() is False


def test_api_key_is_secret():
    entry = EnvEntry(key="API_KEY", value="abc", line_number=1, raw="API_KEY=abc")
    assert entry.is_secret() is True


def test_parse_env_file(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\nBAZ=qux\n", encoding="utf-8")
    env = parse_env_file(env_file)
    assert env.path == env_file
    assert env.as_dict == {"FOO": "bar", "BAZ": "qux"}


def test_empty_file():
    env = parse_env_string("")
    assert env.entries == []


def test_only_comments():
    env = parse_env_string("# just a comment\n# another\n")
    assert env.entries == []

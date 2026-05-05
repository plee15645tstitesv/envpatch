"""Tests for envpatch.export"""
import json
import pytest

from envpatch.parser import EnvFile, EnvEntry
from envpatch.export import ExportFormat, export_shell, export_json, export_docker, export_env


def _entry(key: str, value: str, *, is_comment: bool = False, is_secret: bool = False) -> EnvEntry:
    return EnvEntry(key=key, value=value, raw=f"{key}={value}", is_comment=is_comment, is_secret=is_secret)


def _file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


# --- shell ---

def test_export_shell_basic():
    env = _file(_entry("HOST", "localhost"), _entry("PORT", "5432"))
    result = export_shell(env)
    assert "export HOST='localhost'" in result
    assert "export PORT='5432'" in result


def test_export_shell_skips_comments():
    comment = EnvEntry(key=None, value=None, raw="# comment", is_comment=True, is_secret=False)
    env = _file(comment, _entry("KEY", "val"))
    result = export_shell(env)
    assert "#" not in result
    assert "export KEY='val'" in result


def test_export_shell_redacts_secrets():
    env = _file(_entry("SECRET_KEY", "supersecret", is_secret=True))
    result = export_shell(env, redact=True)
    assert "supersecret" not in result
    assert "SECRET_KEY" in result


def test_export_shell_quotes_special_chars():
    env = _file(_entry("MSG", "hello world"))
    result = export_shell(env)
    assert "export MSG='hello world'" in result


# --- json ---

def test_export_json_basic():
    env = _file(_entry("A", "1"), _entry("B", "2"))
    data = json.loads(export_json(env))
    assert data == {"A": "1", "B": "2"}


def test_export_json_skips_comments():
    comment = EnvEntry(key=None, value=None, raw="# hi", is_comment=True, is_secret=False)
    env = _file(comment, _entry("X", "y"))
    data = json.loads(export_json(env))
    assert data == {"X": "y"}


def test_export_json_redacts_secrets():
    env = _file(_entry("DB_PASSWORD", "s3cr3t", is_secret=True))
    data = json.loads(export_json(env, redact=True))
    assert data["DB_PASSWORD"] != "s3cr3t"


# --- docker ---

def test_export_docker_basic():
    env = _file(_entry("FOO", "bar"), _entry("BAZ", "qux"))
    result = export_docker(env)
    assert "FOO=bar" in result
    assert "BAZ=qux" in result


def test_export_docker_no_quotes():
    env = _file(_entry("MSG", "hello world"))
    result = export_docker(env)
    assert result.strip() == "MSG=hello world"


# --- dispatch ---

def test_export_env_dispatches_shell():
    env = _file(_entry("K", "v"))
    assert export_env(env, ExportFormat.SHELL) == export_shell(env)


def test_export_env_dispatches_json():
    env = _file(_entry("K", "v"))
    assert export_env(env, ExportFormat.JSON) == export_json(env)


def test_export_env_dispatches_docker():
    env = _file(_entry("K", "v"))
    assert export_env(env, ExportFormat.DOCKER) == export_docker(env)


def test_export_env_unknown_format_raises():
    env = _file(_entry("K", "v"))
    with pytest.raises((ValueError, AttributeError)):
        export_env(env, "xml")  # type: ignore[arg-type]

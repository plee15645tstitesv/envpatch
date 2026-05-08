"""Tests for envpatch.flatten."""
from __future__ import annotations

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.flatten import flatten, FlattenEntry, FlattenResult


def _entry(key: str, value: str, *, secret: bool = False) -> EnvEntry:
    return EnvEntry(key=key, value=value, is_comment=False, is_secret=secret, raw=f"{key}={value}")


def _comment() -> EnvEntry:
    return EnvEntry(key="", value="", is_comment=True, is_secret=False, raw="# comment")


def _file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


# ---------------------------------------------------------------------------
# Basic behaviour
# ---------------------------------------------------------------------------

def test_flatten_single_layer_returns_all_keys():
    f = _file(_entry("A", "1"), _entry("B", "2"))
    result = flatten([("base", f)])
    assert result.ok()
    keys = [e.key for e in result.entries]
    assert keys == ["A", "B"]


def test_flatten_later_layer_wins():
    base = _file(_entry("HOST", "localhost"))
    prod = _file(_entry("HOST", "prod.example.com"))
    result = flatten([("base", base), ("prod", prod)])
    winner = result.winner("HOST")
    assert winner is not None
    assert winner.value == "prod.example.com"
    assert winner.source == "prod"


def test_flatten_loser_annotated_with_overridden_by():
    base = _file(_entry("X", "old"))
    override = _file(_entry("X", "new"))
    result = flatten([("base", base), ("override", override)])
    losers = [e for e in result.provenance["X"] if e.overridden_by is not None]
    assert len(losers) == 1
    assert losers[0].source == "base"
    assert losers[0].overridden_by == "override"


def test_flatten_unique_key_has_no_overridden_by():
    f = _file(_entry("ONLY", "here"))
    result = flatten([("base", f)])
    entry = result.winner("ONLY")
    assert entry is not None
    assert entry.overridden_by is None


def test_flatten_comments_are_skipped():
    f = _file(_comment(), _entry("A", "1"), _comment())
    result = flatten([("base", f)])
    assert len(result.entries) == 1
    assert result.entries[0].key == "A"


def test_flatten_skip_secrets_excludes_secret_keys():
    f = _file(_entry("API_KEY", "s3cr3t", secret=True), _entry("HOST", "localhost"))
    result = flatten([("base", f)], skip_secrets=True)
    keys = [e.key for e in result.entries]
    assert "API_KEY" not in keys
    assert "HOST" in keys


def test_flatten_skip_secrets_false_includes_secret_keys():
    f = _file(_entry("API_KEY", "s3cr3t", secret=True))
    result = flatten([("base", f)], skip_secrets=False)
    assert result.winner("API_KEY") is not None


def test_flatten_sources_for_returns_all_labels():
    base = _file(_entry("DB", "sqlite"))
    dev = _file(_entry("DB", "postgres"))
    prod = _file(_entry("DB", "aurora"))
    result = flatten([("base", base), ("dev", dev), ("prod", prod)])
    assert result.sources_for("DB") == ["base", "dev", "prod"]


def test_flatten_sources_for_missing_key_returns_empty():
    f = _file(_entry("A", "1"))
    result = flatten([("base", f)])
    assert result.sources_for("MISSING") == []


def test_flatten_winner_missing_key_returns_none():
    f = _file(_entry("A", "1"))
    result = flatten([("base", f)])
    assert result.winner("NOPE") is None


def test_flatten_as_dict_structure():
    f = _file(_entry("K", "v"))
    result = flatten([("env", f)])
    d = result.as_dict()
    assert "entries" in d
    assert "provenance" in d
    assert d["entries"][0]["key"] == "K"


def test_flatten_key_order_follows_first_appearance():
    base = _file(_entry("Z", "last"), _entry("A", "first"))
    override = _file(_entry("A", "overridden"))
    result = flatten([("base", base), ("override", override)])
    keys = [e.key for e in result.entries]
    assert keys == ["Z", "A"]

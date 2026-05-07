"""Tests for envpatch.chain and envpatch.format_chain."""
from __future__ import annotations

import pytest

from envpatch.parser import EnvEntry, EnvFile
from envpatch.chain import chain, ChainResult
from envpatch.format_chain import (
    format_chain_header,
    format_chain_summary,
    format_chain_source_map,
    format_chain_report,
)


def _entry(key: str, value: str, secret: bool = False) -> EnvEntry:
    return EnvEntry(key=key, value=value, secret=secret, comment=False, raw=f"{key}={value}")


def _comment(text: str = "# note") -> EnvEntry:
    return EnvEntry(key=None, value=None, secret=False, comment=True, raw=text)


def _file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


# --- chain() ---

def test_chain_single_file_returns_all_keys():
    f = _file(_entry("A", "1"), _entry("B", "2"))
    result = chain([f], names=["base"])
    keys = {e.key for e in result.entries if e.key}
    assert keys == {"A", "B"}


def test_chain_later_file_wins():
    base = _file(_entry("A", "base"))
    override = _file(_entry("A", "override"))
    result = chain([base, override], names=["base", "override"])
    assert result.source_map["A"] == "override"
    value = next(e.value for e in result.entries if e.key == "A")
    assert value == "override"


def test_chain_earlier_key_preserved_when_not_overridden():
    base = _file(_entry("X", "from_base"), _entry("Y", "shared"))
    patch = _file(_entry("Y", "patched"))
    result = chain([base, patch], names=["base", "patch"])
    assert result.source_map["X"] == "base"
    assert result.source_map["Y"] == "patch"


def test_chain_source_map_tracks_provenance():
    a = _file(_entry("K1", "v1"))
    b = _file(_entry("K2", "v2"))
    result = chain([a, b], names=["a", "b"])
    assert result.source_map == {"K1": "a", "K2": "b"}


def test_chain_default_names_generated():
    f = _file(_entry("Z", "1"))
    result = chain([f])
    assert result.chain_names == ["file0"]


def test_chain_names_length_mismatch_raises():
    f = _file(_entry("A", "1"))
    with pytest.raises(ValueError):
        chain([f], names=["x", "y"])


def test_chain_empty_files_returns_empty_result():
    result = chain([], names=[])
    assert result.entries == []
    assert result.source_map == {}


def test_chain_comments_skipped_by_default():
    f = _file(_comment("# hello"), _entry("A", "1"))
    result = chain([f], names=["base"])
    assert all(not e.comment for e in result.entries)


def test_chain_as_env_file_returns_env_file_instance():
    f = _file(_entry("A", "1"))
    result = chain([f], names=["base"])
    env = result.as_env_file()
    assert hasattr(env, "entries")


def test_chain_total_keys_counts_non_comment_entries():
    f = _file(_entry("A", "1"), _entry("B", "2"))
    result = chain([f], names=["base"])
    assert result.total_keys() == 2


# --- format_chain ---

def test_format_chain_header_contains_all_names():
    result = ChainResult(entries=[], source_map={}, chain_names=["base", "staging", "local"])
    out = format_chain_header(result.chain_names)
    assert "base" in out
    assert "staging" in out
    assert "local" in out


def test_format_chain_summary_shows_key_count():
    f = _file(_entry("A", "1"), _entry("B", "2"))
    result = chain([f], names=["base"])
    out = format_chain_summary(result)
    assert "2" in out


def test_format_chain_source_map_lists_keys():
    f = _file(_entry("MY_KEY", "val"))
    result = chain([f], names=["env"])
    out = format_chain_source_map(result)
    assert "MY_KEY" in out
    assert "env" in out


def test_format_chain_source_map_empty():
    result = ChainResult(entries=[], source_map={}, chain_names=[])
    out = format_chain_source_map(result)
    assert "no keys" in out


def test_format_chain_report_no_colour():
    f = _file(_entry("PORT", "8080"))
    result = chain([f], names=["base"])
    out = format_chain_report(result, colour=False)
    assert "PORT" in out
    assert "base" in out
    assert "\033[" not in out


def test_format_chain_report_with_colour_contains_ansi():
    f = _file(_entry("PORT", "8080"))
    result = chain([f], names=["base"])
    out = format_chain_report(result, colour=True)
    assert "\033[" in out

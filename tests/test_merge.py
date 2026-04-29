"""Tests for envpatch.merge module."""

import pytest

from envpatch.merge import ConflictStrategy, MergeConflictError, merge
from envpatch.parser import EnvFile


def _make(text: str) -> EnvFile:
    return EnvFile.parse(text)


def test_merge_adds_new_keys_from_patch():
    base = _make("FOO=bar")
    patch = _make("BAZ=qux")
    result = merge(base, patch)
    d = result.as_dict()
    assert d["FOO"] == "bar"
    assert d["BAZ"] == "qux"


def test_merge_respects_add_missing_false():
    base = _make("FOO=bar")
    patch = _make("BAZ=qux")
    result = merge(base, patch, add_missing=False)
    assert "BAZ" not in result.as_dict()


def test_merge_patch_wins_by_default():
    base = _make("FOO=old")
    patch = _make("FOO=new")
    result = merge(base, patch, strategy=ConflictStrategy.USE_PATCH)
    assert result.as_dict()["FOO"] == "new"


def test_merge_base_wins_with_use_base():
    base = _make("FOO=old")
    patch = _make("FOO=new")
    result = merge(base, patch, strategy=ConflictStrategy.USE_BASE)
    assert result.as_dict()["FOO"] == "old"


def test_merge_error_strategy_raises():
    base = _make("FOO=old")
    patch = _make("FOO=new")
    with pytest.raises(MergeConflictError) as exc_info:
        merge(base, patch, strategy=ConflictStrategy.ERROR)
    assert exc_info.value.key == "FOO"
    assert exc_info.value.base_value == "old"
    assert exc_info.value.patch_value == "new"


def test_merge_same_value_no_conflict():
    base = _make("FOO=same")
    patch = _make("FOO=same")
    result = merge(base, patch, strategy=ConflictStrategy.ERROR)
    assert result.as_dict()["FOO"] == "same"


def test_merge_preserves_base_only_keys():
    base = _make("KEEP=yes\nFOO=bar")
    patch = _make("FOO=baz")
    result = merge(base, patch)
    assert "KEEP" in result.as_dict()


def test_merge_result_is_envfile():
    base = _make("A=1")
    patch = _make("B=2")
    result = merge(base, patch)
    assert isinstance(result, EnvFile)
    assert set(result.as_dict().keys()) == {"A", "B"}

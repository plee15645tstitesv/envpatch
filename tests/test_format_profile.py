"""Tests for envpatch.format_profile."""
from __future__ import annotations

import pytest

from envpatch.profile import Profile, ProfileStore
from envpatch.format_profile import (
    format_profile_list,
    format_profile_saved,
    format_profile_deleted,
    format_profile_not_found,
    format_profile_applied,
)


def _profile(name: str = "dev", env: str = "development", **overrides: str) -> Profile:
    return Profile(name=name, env=env, overrides=dict(overrides))


def test_list_empty_no_colour():
    store = ProfileStore()
    out = format_profile_list(store, colour=False)
    assert "No profiles" in out


def test_list_shows_profile_name():
    store = ProfileStore(profiles=[_profile("staging", "staging", FOO="bar")])
    out = format_profile_list(store, colour=False)
    assert "staging" in out


def test_list_shows_override_count():
    store = ProfileStore(profiles=[_profile("x", "y", A="1", B="2")])
    out = format_profile_list(store, colour=False)
    assert "2 override" in out


def test_list_with_colour_contains_ansi():
    store = ProfileStore(profiles=[_profile()])
    out = format_profile_list(store, colour=True)
    assert "\033[" in out


def test_saved_no_colour():
    p = _profile("ci", "ci", KEY="val")
    out = format_profile_saved(p, colour=False)
    assert "ci" in out
    assert "1 override" in out


def test_saved_with_colour_contains_ansi():
    p = _profile()
    out = format_profile_saved(p, colour=True)
    assert "\033[" in out


def test_deleted_no_colour():
    out = format_profile_deleted("old-profile", colour=False)
    assert "old-profile" in out
    assert "deleted" in out


def test_deleted_with_colour_contains_ansi():
    out = format_profile_deleted("x", colour=True)
    assert "\033[" in out


def test_not_found_no_colour():
    out = format_profile_not_found("ghost", colour=False)
    assert "ghost" in out
    assert "not found" in out


def test_applied_shows_name_and_count():
    p = _profile("prod", "production", A="1")
    out = format_profile_applied(p, key_count=5, colour=False)
    assert "prod" in out
    assert "5 key" in out


def test_applied_with_colour_contains_ansi():
    p = _profile()
    out = format_profile_applied(p, key_count=3, colour=True)
    assert "\033[" in out

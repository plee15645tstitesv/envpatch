"""CLI command handlers for profile management."""
from __future__ import annotations

import argparse
from pathlib import Path

from envpatch.profile import (
    Profile,
    load_profiles,
    save_profiles,
    apply_profile,
)
from envpatch.parser import EnvFile
from envpatch.format_profile import (
    format_profile_list,
    format_profile_saved,
    format_profile_deleted,
    format_profile_not_found,
    format_profile_applied,
)


def cmd_profile_list(args: argparse.Namespace) -> int:
    directory = Path(args.dir)
    store = load_profiles(directory)
    colour = getattr(args, "colour", False)
    print(format_profile_list(store, colour=colour))
    return 0


def cmd_profile_save(args: argparse.Namespace) -> int:
    directory = Path(args.dir)
    store = load_profiles(directory)
    overrides: dict[str, str] = {}
    for item in args.set or []:
        if "=" not in item:
            print(f"Invalid override '{item}': expected KEY=VALUE")
            return 1
        key, _, value = item.partition("=")
        overrides[key.strip()] = value.strip()
    profile = Profile(name=args.name, env=args.env, overrides=overrides)
    store.add(profile)
    save_profiles(store, directory)
    colour = getattr(args, "colour", False)
    print(format_profile_saved(profile, colour=colour))
    return 0


def cmd_profile_delete(args: argparse.Namespace) -> int:
    directory = Path(args.dir)
    store = load_profiles(directory)
    colour = getattr(args, "colour", False)
    if store.remove(args.name):
        save_profiles(store, directory)
        print(format_profile_deleted(args.name, colour=colour))
        return 0
    print(format_profile_not_found(args.name, colour=colour))
    return 1


def cmd_profile_apply(args: argparse.Namespace) -> int:
    directory = Path(args.dir)
    store = load_profiles(directory)
    colour = getattr(args, "colour", False)
    profile = store.get(args.name)
    if profile is None:
        print(format_profile_not_found(args.name, colour=colour))
        return 1
    base = EnvFile.parse(Path(args.file).read_text())
    result = apply_profile(base, profile)
    output_path = Path(args.output) if args.output else None
    rendered = "".join(e.raw + "\n" for e in result.entries)
    if output_path:
        output_path.write_text(rendered)
    else:
        print(rendered, end="")
    key_count = sum(1 for e in result.entries if not e.is_comment and e.key)
    print(format_profile_applied(profile, key_count=key_count, colour=colour))
    return 0

"""Command-line interface for envpatch."""

import argparse
import sys
from envpatch.parser import EnvFile
from envpatch.diff import diff
from envpatch.merge import merge, ConflictStrategy
from envpatch.format import format_diff, format_env_file


def cmd_diff(args: argparse.Namespace) -> int:
    base = EnvFile.from_file(args.base)
    other = EnvFile.from_file(args.other)
    entries = diff(base, other)
    output = format_diff(
        entries,
        color=not args.no_color,
        redact=not args.show_secrets,
    )
    print(output)
    return 0


def cmd_merge(args: argparse.Namespace) -> int:
    base = EnvFile.from_file(args.base)
    patch = EnvFile.from_file(args.patch)

    strategy_map = {
        "patch": ConflictStrategy.PATCH_WINS,
        "base": ConflictStrategy.BASE_WINS,
        "error": ConflictStrategy.ERROR,
    }
    strategy = strategy_map.get(args.strategy, ConflictStrategy.PATCH_WINS)

    try:
        result = merge(
            base,
            patch,
            conflict_strategy=strategy,
            add_missing=not args.no_add,
        )
    except Exception as exc:  # MergeConflictError
        print(f"Merge conflict: {exc}", file=sys.stderr)
        return 1

    output = format_env_file(result, redact=False)
    if args.output:
        with open(args.output, "w") as fh:
            fh.write(output + "\n")
    else:
        print(output)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envpatch",
        description="Diff and merge .env files without leaking secrets.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    diff_p = sub.add_parser("diff", help="Show diff between two .env files")
    diff_p.add_argument("base", help="Base .env file")
    diff_p.add_argument("other", help="Other .env file to compare")
    diff_p.add_argument("--no-color", action="store_true", help="Disable ANSI color")
    diff_p.add_argument("--show-secrets", action="store_true", help="Show secret values")
    diff_p.set_defaults(func=cmd_diff)

    merge_p = sub.add_parser("merge", help="Merge patch .env into base .env")
    merge_p.add_argument("base", help="Base .env file")
    merge_p.add_argument("patch", help="Patch .env file")
    merge_p.add_argument("-o", "--output", default=None, help="Output file (default: stdout)")
    merge_p.add_argument(
        "--strategy",
        choices=["patch", "base", "error"],
        default="patch",
        help="Conflict resolution strategy",
    )
    merge_p.add_argument("--no-add", action="store_true", help="Do not add missing keys")
    merge_p.set_defaults(func=cmd_merge)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()

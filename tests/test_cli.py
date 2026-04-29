"""Tests for envpatch.cli module."""

import os
import pytest
from unittest.mock import patch, MagicMock
from argparse import Namespace
from envpatch.cli import build_parser, cmd_diff, cmd_merge
from envpatch.parser import EnvEntry, EnvFile


def _make_file(pairs, path="test.env"):
    entries = [
        EnvEntry(key=k, value=v, raw=f"{k}={v}", is_secret=("SECRET" in k or "PASSWORD" in k))
        for k, v in pairs
    ]
    return EnvFile(entries=entries, path=path)


class TestBuildParser:
    def test_diff_subcommand_parsed(self):
        parser = build_parser()
        args = parser.parse_args(["diff", "base.env", "other.env"])
        assert args.command == "diff"
        assert args.base == "base.env"
        assert args.other == "other.env"
        assert not args.no_color
        assert not args.show_secrets

    def test_merge_subcommand_parsed(self):
        parser = build_parser()
        args = parser.parse_args(["merge", "base.env", "patch.env", "--strategy", "base"])
        assert args.command == "merge"
        assert args.strategy == "base"

    def test_merge_output_flag(self):
        parser = build_parser()
        args = parser.parse_args(["merge", "a.env", "b.env", "-o", "out.env"])
        assert args.output == "out.env"

    def test_no_subcommand_raises(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])


class TestCmdDiff:
    def test_diff_prints_output(self, capsys):
        base = _make_file([("FOO", "bar")])
        other = _make_file([("FOO", "baz")])
        args = Namespace(base="base.env", other="other.env", no_color=True, show_secrets=False)
        with patch("envpatch.cli.EnvFile.from_file", side_effect=[base, other]):
            result = cmd_diff(args)
        assert result == 0
        captured = capsys.readouterr()
        assert "FOO" in captured.out

    def test_diff_returns_zero(self):
        base = _make_file([("A", "1")])
        other = _make_file([("A", "1")])
        args = Namespace(base="b.env", other="o.env", no_color=True, show_secrets=False)
        with patch("envpatch.cli.EnvFile.from_file", side_effect=[base, other]):
            assert cmd_diff(args) == 0


class TestCmdMerge:
    def test_merge_stdout_output(self, capsys):
        base = _make_file([("FOO", "bar")])
        patch_file = _make_file([("FOO", "baz"), ("NEW", "val")])
        args = Namespace(
            base="base.env", patch="patch.env",
            output=None, strategy="patch", no_add=False,
        )
        with patch("envpatch.cli.EnvFile.from_file", side_effect=[base, patch_file]):
            result = cmd_merge(args)
        assert result == 0
        captured = capsys.readouterr()
        assert "FOO" in captured.out

    def test_merge_writes_file(self, tmp_path):
        base = _make_file([("X", "1")])
        patch_file = _make_file([("X", "2")])
        out_path = str(tmp_path / "out.env")
        args = Namespace(
            base="base.env", patch="patch.env",
            output=out_path, strategy="patch", no_add=False,
        )
        with patch("envpatch.cli.EnvFile.from_file", side_effect=[base, patch_file]):
            result = cmd_merge(args)
        assert result == 0
        assert os.path.exists(out_path)
        content = open(out_path).read()
        assert "X=2" in content

    def test_merge_conflict_error_returns_one(self, capsys):
        from envpatch.merge import MergeConflictError
        base = _make_file([("KEY", "a")])
        patch_file = _make_file([("KEY", "b")])
        args = Namespace(
            base="base.env", patch="patch.env",
            output=None, strategy="error", no_add=False,
        )
        with patch("envpatch.cli.EnvFile.from_file", side_effect=[base, patch_file]):
            result = cmd_merge(args)
        assert result == 1

"""Tests for CLI argument parser."""

import pytest

from token_tracker.cli import build_parser, main


def test_parser_defaults():
    parser = build_parser()
    args = parser.parse_args([])
    assert args.source == "auto"
    assert args.days == 30
    assert args.dry_run is False
    assert args.baseline is None
    assert args.compare is None
    assert args.validate is False
    assert args.open is False
    assert args.with_subagents is False


def test_parser_source_choices():
    parser = build_parser()
    for src in ("opencode", "claude-code", "auto"):
        args = parser.parse_args(["--source", src])
        assert args.source == src


def test_parser_days():
    parser = build_parser()
    args = parser.parse_args(["--days", "7"])
    assert args.days == 7


def test_parser_dry_run():
    parser = build_parser()
    args = parser.parse_args(["--dry-run"])
    assert args.dry_run is True


def test_parser_baseline():
    parser = build_parser()
    args = parser.parse_args(["--baseline", "pre-experiment"])
    assert args.baseline == "pre-experiment"


def test_parser_compare():
    parser = build_parser()
    args = parser.parse_args(["--compare", "pre-experiment"])
    assert args.compare == "pre-experiment"


def test_parser_validate():
    parser = build_parser()
    args = parser.parse_args(["--validate"])
    assert args.validate is True


def test_parser_open():
    parser = build_parser()
    args = parser.parse_args(["--open"])
    assert args.open is True


def test_parser_with_subagents():
    parser = build_parser()
    args = parser.parse_args(["--with-subagents"])
    assert args.with_subagents is True


def test_parser_output():
    parser = build_parser()
    args = parser.parse_args(["--output", "/tmp/test.html"])
    assert args.output == "/tmp/test.html"


def test_parser_db():
    parser = build_parser()
    args = parser.parse_args(["--db", "/path/to/custom.db"])
    assert args.db == "/path/to/custom.db"


def test_parser_combination():
    parser = build_parser()
    args = parser.parse_args([
        "--source", "opencode",
        "--days", "14",
        "--dry-run",
        "--baseline", "weekly",
    ])
    assert args.source == "opencode"
    assert args.days == 14
    assert args.dry_run is True
    assert args.baseline == "weekly"


def test_main_exits_on_missing_db(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--db", str(tmp_path / "nonexistent.db")])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_cli_short_flags():
    parser = build_parser()
    args = parser.parse_args(["-d", "7", "-o", "/tmp/out.html"])
    assert args.days == 7
    assert args.output == "/tmp/out.html"
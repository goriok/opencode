"""Tests for shortcuts install — idempotency and correctness."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from oc.cli import app
from oc.commands.shortcuts import _MARKER, _install_to, _ZSH_BASH_BLOCK

runner = CliRunner()


def test_install_to_creates_file(tmp_path):
    config = tmp_path / ".zshrc"
    _install_to(config, _ZSH_BASH_BLOCK, "zsh")
    assert config.exists()
    assert _MARKER in config.read_text()


def test_install_to_idempotent(tmp_path):
    config = tmp_path / ".zshrc"
    _install_to(config, _ZSH_BASH_BLOCK, "zsh")
    first_content = config.read_text()
    _install_to(config, _ZSH_BASH_BLOCK, "zsh")
    # file must not grow — no duplicate block
    assert config.read_text() == first_content


def test_install_to_appends_to_existing_file(tmp_path):
    config = tmp_path / ".zshrc"
    config.write_text("# existing content\n")
    _install_to(config, _ZSH_BASH_BLOCK, "zsh")
    content = config.read_text()
    assert "# existing content" in content
    assert _MARKER in content


def test_install_to_creates_parent_dirs(tmp_path):
    config = tmp_path / "nested" / "dir" / "config.fish"
    _install_to(config, _ZSH_BASH_BLOCK, "fish")
    assert config.exists()


def test_cli_shortcuts_install_zsh(tmp_path, monkeypatch):
    config = tmp_path / ".zshrc"
    monkeypatch.setattr("oc.commands.shortcuts.Path.home", lambda: tmp_path)
    result = runner.invoke(app, ["shortcuts", "install", "--shell", "zsh"])
    assert result.exit_code == 0

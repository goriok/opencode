"""Smoke tests for the oc CLI entry point."""

from typer.testing import CliRunner

from ocx.cli import app

runner = CliRunner()


def test_help_exits_ok():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "agents" in result.output
    assert "litellm" in result.output
    assert "shortcuts" in result.output
    assert "configs" in result.output
    assert "git" in result.output
    assert "setup" in result.output


def test_agents_help():
    result = runner.invoke(app, ["agents", "--help"])
    assert result.exit_code == 0
    assert "sync" in result.output
    assert "install" in result.output
    assert "count" in result.output


def test_litellm_help():
    result = runner.invoke(app, ["litellm", "--help"])
    assert result.exit_code == 0
    assert "up" in result.output
    assert "down" in result.output
    assert "status" in result.output
    assert "models" in result.output
    assert "env-init" in result.output


def test_shortcuts_help():
    result = runner.invoke(app, ["shortcuts", "--help"])
    assert result.exit_code == 0
    assert "install" in result.output


def test_configs_check(tmp_path, monkeypatch):
    monkeypatch.setattr("ocx.commands.configs.OPENCODE_DIR", tmp_path)
    result = runner.invoke(app, ["configs", "check"])
    assert result.exit_code == 0
    assert "opencode.jsonc" in result.output


def test_agents_count(tmp_path, monkeypatch):
    (tmp_path / "alan-turing.md").write_text("# agent")
    (tmp_path / "grace-hopper.md").write_text("# agent")
    monkeypatch.setattr("ocx.commands.agents.AGENTS_DIR", tmp_path)
    result = runner.invoke(app, ["agents", "count"])
    assert result.exit_code == 0
    assert "2" in result.output

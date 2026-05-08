"""Smoke tests for oc tier CLI commands (list, show, current, diff, set)."""

import json
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from oc.cli import app
from oc.paths import TIERS_DIR

runner = CliRunner()


@pytest.fixture
def tmp_state(tmp_path, monkeypatch):
    """Redirect TIER_STATE to a temp path so tests don't touch the real state file."""
    import oc.commands.tier as tier_mod
    import oc.paths as paths_mod

    fake_state = tmp_path / ".tier-state.json"
    monkeypatch.setattr(paths_mod, "TIER_STATE", fake_state)
    monkeypatch.setattr(tier_mod, "TIER_STATE", fake_state)
    return fake_state


def test_tier_list_shows_all_tiers():
    result = runner.invoke(app, ["tier", "list"])
    assert result.exit_code == 0
    for name in ("free", "low", "med", "high", "max"):
        assert name in result.output


def test_tier_show_med():
    result = runner.invoke(app, ["tier", "show", "med"])
    assert result.exit_code == 0
    assert "med" in result.output
    assert "zai/glm-4.7" in result.output or "zai/glm-5.1" in result.output


def test_tier_show_unknown_exits_nonzero():
    result = runner.invoke(app, ["tier", "show", "nonexistent"])
    assert result.exit_code != 0


def test_tier_current_no_state(tmp_state):
    result = runner.invoke(app, ["tier", "current"])
    assert result.exit_code != 0


def test_tier_diff_free_max():
    result = runner.invoke(app, ["tier", "diff", "free", "max"])
    assert result.exit_code == 0
    assert "claude-opus-4-7" in result.output
    assert "opencode-go" in result.output


def test_tier_set_dry_run_no_writes(tmp_path, monkeypatch):
    """--dry-run must not write any files."""
    import oc.commands.tier as tier_mod
    import oc.paths as paths_mod

    fake_plugin = tmp_path / "oh-my-openagent.jsonc"
    fake_litellm = tmp_path / "config.yaml"
    fake_state = tmp_path / ".tier-state.json"

    # Copy real files so render has something to parse.
    real_plugin = Path.home() / ".config" / "opencode" / "oh-my-openagent.jsonc"
    real_litellm = Path.home() / ".config" / "opencode" / "litellm" / "config.yaml"
    if not real_plugin.exists() or not real_litellm.exists():
        pytest.skip("Real config files not present")

    fake_plugin.write_text(real_plugin.read_text())
    fake_litellm.write_text(real_litellm.read_text())

    monkeypatch.setattr(paths_mod, "OH_MY_OPENAGENT", fake_plugin)
    monkeypatch.setattr(paths_mod, "LITELLM_CONFIG", fake_litellm)
    monkeypatch.setattr(paths_mod, "TIER_STATE", fake_state)
    monkeypatch.setattr(tier_mod, "OH_MY_OPENAGENT", fake_plugin)
    monkeypatch.setattr(tier_mod, "LITELLM_CONFIG", fake_litellm)
    monkeypatch.setattr(tier_mod, "TIER_STATE", fake_state)

    original_plugin_mtime = fake_plugin.stat().st_mtime
    original_litellm_mtime = fake_litellm.stat().st_mtime

    result = runner.invoke(app, ["tier", "set", "med", "--dry-run"])
    assert result.exit_code == 0

    # Files must not have been modified.
    assert fake_plugin.stat().st_mtime == original_plugin_mtime
    assert fake_litellm.stat().st_mtime == original_litellm_mtime
    assert not fake_state.exists()


def test_tier_set_writes_state(tmp_path, monkeypatch):
    """oc tier set must update the state file with the active tier name."""
    import oc.commands.tier as tier_mod
    import oc.paths as paths_mod

    real_plugin = Path.home() / ".config" / "opencode" / "oh-my-openagent.jsonc"
    real_litellm = Path.home() / ".config" / "opencode" / "litellm" / "config.yaml"
    if not real_plugin.exists() or not real_litellm.exists():
        pytest.skip("Real config files not present")

    fake_plugin = tmp_path / "oh-my-openagent.jsonc"
    fake_litellm = tmp_path / "config.yaml"
    fake_state = tmp_path / ".tier-state.json"
    fake_plugin.write_text(real_plugin.read_text())
    fake_litellm.write_text(real_litellm.read_text())

    monkeypatch.setattr(paths_mod, "OH_MY_OPENAGENT", fake_plugin)
    monkeypatch.setattr(paths_mod, "LITELLM_CONFIG", fake_litellm)
    monkeypatch.setattr(paths_mod, "TIER_STATE", fake_state)
    monkeypatch.setattr(tier_mod, "OH_MY_OPENAGENT", fake_plugin)
    monkeypatch.setattr(tier_mod, "LITELLM_CONFIG", fake_litellm)
    monkeypatch.setattr(tier_mod, "TIER_STATE", fake_state)

    result = runner.invoke(app, ["tier", "set", "low"])
    assert result.exit_code == 0
    assert fake_state.exists()
    state = json.loads(fake_state.read_text())
    assert state["active"] == "low"


def test_tier_set_validator_catches_missing_agent(tmp_path, monkeypatch):
    """oc tier set must fail if the tier YAML is missing an agent from the base."""
    import oc.commands.tier as tier_mod
    import oc.paths as paths_mod

    real_plugin = Path.home() / ".config" / "opencode" / "oh-my-openagent.jsonc"
    if not real_plugin.exists():
        pytest.skip("Real config files not present")

    # Minimal valid oh-my-openagent with an extra agent not in any tier.
    fake_plugin = tmp_path / "oh-my-openagent.jsonc"
    fake_litellm = tmp_path / "config.yaml"
    fake_state = tmp_path / ".tier-state.json"

    import json as json_mod
    base = {
        "agents": {"sisyphus": {"model": "x"}, "nonexistent-agent": {"model": "x"}},
        "categories": {"quick": {"model": "x"}},
    }
    fake_plugin.write_text(json_mod.dumps(base))

    real_litellm = Path.home() / ".config" / "opencode" / "litellm" / "config.yaml"
    if real_litellm.exists():
        fake_litellm.write_text(real_litellm.read_text())
    else:
        fake_litellm.write_text("model_list: []\ngeneral_settings: {}\n")

    monkeypatch.setattr(paths_mod, "OH_MY_OPENAGENT", fake_plugin)
    monkeypatch.setattr(paths_mod, "LITELLM_CONFIG", fake_litellm)
    monkeypatch.setattr(paths_mod, "TIER_STATE", fake_state)
    monkeypatch.setattr(tier_mod, "OH_MY_OPENAGENT", fake_plugin)
    monkeypatch.setattr(tier_mod, "LITELLM_CONFIG", fake_litellm)
    monkeypatch.setattr(tier_mod, "TIER_STATE", fake_state)

    result = runner.invoke(app, ["tier", "set", "med"])
    assert result.exit_code != 0
    assert "nonexistent-agent" in result.output

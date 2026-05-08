"""Tests for src/oc/tier_apply.py — pure render functions, no filesystem I/O."""

import json
import textwrap

import pytest
import yaml

from oc.tier_apply import loads_jsonc, parse_jsonc, render_litellm, render_plugin, validate_tier

# ── Fixtures ──────────────────────────────────────────────────────────────────

BASE_PLUGIN = {
    "$schema": "https://example.com/schema.json",
    "disabled_hooks": [],
    "disabled_agents": [],
    "disabled_skills": [],
    "disabled_mcps": [],
    "agents": {
        "sisyphus": {"model": "zai/glm-4.7", "fallback_models": ["opencode-go/deepseek-v4-pro"]},
        "oracle": {"model": "zai/glm-5.1", "thinking": {"type": "enabled"}, "fallback_models": ["opencode-go/glm-5.1"]},
    },
    "categories": {
        "quick": {"model": "zai/glm-4.5-air", "fallback_models": ["opencode-go/deepseek-v4-flash"]},
        "ultrabrain": {"model": "zai/glm-5.1", "thinking": {"type": "enabled"}, "fallback_models": ["opencode-go/glm-5.1"]},
    },
    "runtime_fallback": {"enabled": True, "max_fallback_attempts": 3},
    "background_task": {"defaultConcurrency": 5},
    "experimental": {"aggressive_truncation": False},
    "hooks": {"thinking_block_validator": {"enabled": True}},
}

SIMPLE_TIER = {
    "name": "test",
    "budget": {"max_usd_month": 10},
    "agents": {
        "sisyphus": {"model": "opencode-go/deepseek-v4-flash", "fallback_models": ["opencode-go/qwen3.5-plus"]},
        "oracle": {"model": "zai/glm-4.7", "thinking": {"type": "enabled"}, "fallback_models": ["opencode-go/glm-5.1"]},
    },
    "categories": {
        "quick": {"model": "opencode-go/deepseek-v4-flash", "fallback_models": []},
        "ultrabrain": {"model": "zai/glm-5.1", "thinking": {"type": "enabled"}, "fallback_models": ["opencode-go/glm-5.1"]},
    },
    "litellm": {"models": ["claude-haiku-4-5-20251001"]},
}

BASE_LITELLM = {
    "model_list": [
        {"model_name": "claude-sonnet-4-6", "litellm_params": {"model": "anthropic/claude-sonnet-4-6", "max_retries": 0}},
    ],
    "litellm_settings": {"callbacks": ["prometheus"]},
    "router_settings": {"routing_strategy": "simple-shuffle"},
    "general_settings": {"master_key": "os.environ/LITELLM_MASTER_KEY"},
}


# ── validate_tier ──────────────────────────────────────────────────────────────

def test_validate_tier_ok():
    validate_tier(SIMPLE_TIER, BASE_PLUGIN)  # should not raise


def test_validate_tier_missing_agent():
    bad_tier = {**SIMPLE_TIER, "agents": {"oracle": SIMPLE_TIER["agents"]["oracle"]}}
    with pytest.raises(ValueError, match="agent 'sisyphus'"):
        validate_tier(bad_tier, BASE_PLUGIN)


def test_validate_tier_missing_category():
    bad_tier = {**SIMPLE_TIER, "categories": {"ultrabrain": SIMPLE_TIER["categories"]["ultrabrain"]}}
    with pytest.raises(ValueError, match="category 'quick'"):
        validate_tier(bad_tier, BASE_PLUGIN)


# ── render_plugin ──────────────────────────────────────────────────────────────

def test_render_plugin_replaces_agents():
    result = render_plugin(SIMPLE_TIER, BASE_PLUGIN)
    assert result["agents"]["sisyphus"]["model"] == "opencode-go/deepseek-v4-flash"
    assert result["agents"]["oracle"]["model"] == "zai/glm-4.7"


def test_render_plugin_thinking_preserved():
    result = render_plugin(SIMPLE_TIER, BASE_PLUGIN)
    assert result["agents"]["oracle"]["thinking"] == {"type": "enabled"}
    # sisyphus has no thinking key in tier → must be absent in output
    assert "thinking" not in result["agents"]["sisyphus"]


def test_render_plugin_passthrough_keys_preserved():
    result = render_plugin(SIMPLE_TIER, BASE_PLUGIN)
    assert result["runtime_fallback"] == BASE_PLUGIN["runtime_fallback"]
    assert result["hooks"] == BASE_PLUGIN["hooks"]
    assert result["disabled_agents"] == []


def test_render_plugin_empty_fallback_omitted():
    result = render_plugin(SIMPLE_TIER, BASE_PLUGIN)
    # quick category has fallback_models: [] → should NOT appear in output
    assert "fallback_models" not in result["categories"]["quick"]


def test_render_plugin_nonempty_fallback_included():
    result = render_plugin(SIMPLE_TIER, BASE_PLUGIN)
    assert result["agents"]["sisyphus"]["fallback_models"] == ["opencode-go/qwen3.5-plus"]


# ── render_litellm ─────────────────────────────────────────────────────────────

def test_render_litellm_model_list_replaced():
    result = render_litellm(SIMPLE_TIER, BASE_LITELLM)
    assert len(result["model_list"]) == 1
    assert result["model_list"][0]["model_name"] == "claude-haiku-4-5-20251001"
    assert result["model_list"][0]["litellm_params"]["model"] == "anthropic/claude-haiku-4-5-20251001"


def test_render_litellm_budget_applied():
    result = render_litellm(SIMPLE_TIER, BASE_LITELLM)
    assert result["general_settings"]["max_budget"] == 10


def test_render_litellm_no_budget_removes_key():
    no_budget_tier = {**SIMPLE_TIER, "budget": {}}
    result = render_litellm(no_budget_tier, BASE_LITELLM)
    assert "max_budget" not in result["general_settings"]


def test_render_litellm_passthrough_preserved():
    result = render_litellm(SIMPLE_TIER, BASE_LITELLM)
    assert result["litellm_settings"] == BASE_LITELLM["litellm_settings"]
    assert result["router_settings"] == BASE_LITELLM["router_settings"]


def test_render_litellm_unknown_model_raises():
    bad_tier = {**SIMPLE_TIER, "litellm": {"models": ["nonexistent-model"]}}
    with pytest.raises(ValueError, match="Unknown model"):
        render_litellm(bad_tier, BASE_LITELLM)


# ── parse_jsonc ────────────────────────────────────────────────────────────────

def test_parse_jsonc_strips_line_comments():
    jsonc = '{"key": "value" // comment\n}'
    parsed = json.loads(parse_jsonc(jsonc))
    assert parsed == {"key": "value"}


def test_parse_jsonc_strips_block_comments():
    jsonc = '/* header */\n{"key": "value"}'
    parsed = json.loads(parse_jsonc(jsonc))
    assert parsed == {"key": "value"}


# ── Round-trip: med.yaml must reproduce current oh-my-openagent.jsonc ─────────

def test_med_tier_round_trip(tmp_path):
    """Applying tiers/med.yaml to current oh-my-openagent.jsonc should produce
    semantically identical agents and categories blocks."""
    import importlib.resources
    from pathlib import Path

    opencode_dir = Path.home() / ".config" / "opencode"
    med_path = opencode_dir / "tiers" / "med.yaml"
    plugin_path = opencode_dir / "oh-my-openagent.jsonc"

    if not med_path.exists() or not plugin_path.exists():
        pytest.skip("tiers/med.yaml or oh-my-openagent.jsonc not found")

    tier = yaml.safe_load(med_path.read_text())
    base = loads_jsonc(plugin_path.read_text())

    validate_tier(tier, base)
    result = render_plugin(tier, base)

    # agents block must be semantically equal.
    for agent_name, base_entry in base["agents"].items():
        result_entry = result["agents"][agent_name]
        assert result_entry["model"] == base_entry["model"], f"agent {agent_name}: model mismatch"
        if "thinking" in base_entry:
            assert result_entry.get("thinking") == base_entry["thinking"], f"agent {agent_name}: thinking mismatch"
        if base_entry.get("fallback_models"):
            assert result_entry.get("fallback_models") == base_entry["fallback_models"], f"agent {agent_name}: fallback mismatch"

    # categories block must be semantically equal.
    for cat_name, base_entry in base["categories"].items():
        result_entry = result["categories"][cat_name]
        assert result_entry["model"] == base_entry["model"], f"category {cat_name}: model mismatch"

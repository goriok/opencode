"""Tests for src/oc/providers.py — pure functions, no filesystem I/O beyond load_catalog."""

from __future__ import annotations

from pathlib import Path

import pytest

from oc.providers import cost_label, load_catalog, resolve_model, validate_eligibility

# ── Fixtures ──────────────────────────────────────────────────────────────────

ZAI_CAT = {
    "provider": "zai",
    "quota_unit": "prompt",
    "models": {
        "glm-4.7": {"multiplier": 1, "tiers": ["low", "med", "high", "max", "zai-lite", "zai-pro", "zai-max"]},
        "glm-5.1": {"multiplier": 2, "thinking_capable": True, "tiers": ["med", "high", "max", "zai-pro", "zai-max"]},
    },
}

GO_CAT = {
    "provider": "opencode-go",
    "quota_unit": "usd_credit",
    "models": {
        "kimi-k2.5": {"usd_per_mtok_in": 0.50, "usd_per_mtok_out": 2.50, "tiers": ["free", "low", "med", "go-only"]},
        "deepseek-v4-flash": {"usd_per_mtok_in": 0.14, "usd_per_mtok_out": 0.28, "tiers": ["free", "low", "med", "go-only"]},
    },
}

COPILOT_CAT = {
    "provider": "copilot",
    "quota_unit": "premium_request",
    "models": {
        "claude-sonnet-4-6": {"multiplier": 1, "tiers": ["max", "copilot-pro+"]},
        "claude-opus-4-7": {"multiplier": 10, "thinking_capable": True, "tiers": ["max", "copilot-pro+"]},
    },
}

ANTHROPIC_CAT = {
    "provider": "anthropic",
    "quota_unit": "usd_token",
    "models": {
        "claude-haiku-4-5-20251001": {"usd_per_mtok_in": 1.00, "usd_per_mtok_out": 5.00, "tiers": ["free", "low", "med", "high", "max"]},
        "claude-sonnet-4-6": {"usd_per_mtok_in": 3.00, "usd_per_mtok_out": 15.00, "tiers": ["med", "high", "max"]},
    },
}

CATALOG = {
    "zai": ZAI_CAT,
    "opencode-go": GO_CAT,
    "copilot": COPILOT_CAT,
    "anthropic": ANTHROPIC_CAT,
}

MED_TIER = {
    "name": "med",
    "agents": {
        "oracle": {"model": "zai/glm-5.1", "thinking": {"type": "enabled"}, "fallback_models": ["opencode-go/kimi-k2.5"]},
        "coder": {"model": "opencode-go/kimi-k2.5", "fallback_models": []},
    },
    "categories": {
        "quick": {"model": "opencode-go/deepseek-v4-flash", "fallback_models": []},
    },
}


# ── resolve_model ──────────────────────────────────────────────────────────────

def test_resolve_model_with_slash():
    assert resolve_model("zai/glm-5.1") == ("zai", "glm-5.1")


def test_resolve_model_no_slash_defaults_anthropic():
    assert resolve_model("claude-sonnet-4-6") == ("anthropic", "claude-sonnet-4-6")


def test_resolve_model_opencode_go():
    assert resolve_model("opencode-go/kimi-k2.5") == ("opencode-go", "kimi-k2.5")


def test_resolve_model_preserves_second_slash():
    # edge: gemini/gemini-3.1-flash-lite-preview — only first slash splits
    assert resolve_model("gemini/gemini-3.1-flash-lite-preview") == ("gemini", "gemini-3.1-flash-lite-preview")


# ── cost_label ─────────────────────────────────────────────────────────────────

def test_cost_label_prompt_multiplier_1():
    assert cost_label(ZAI_CAT, "glm-4.7") == "1× quota"


def test_cost_label_prompt_multiplier_2():
    assert cost_label(ZAI_CAT, "glm-5.1") == "2× quota"


def test_cost_label_premium_request():
    assert cost_label(COPILOT_CAT, "claude-opus-4-7") == "10 premium req"


def test_cost_label_usd_credit():
    assert cost_label(GO_CAT, "kimi-k2.5") == "$0.5/$2.5 /Mtok"


def test_cost_label_usd_token():
    assert cost_label(ANTHROPIC_CAT, "claude-sonnet-4-6") == "$3.0/$15.0 /Mtok"


def test_cost_label_unknown_model():
    assert cost_label(ZAI_CAT, "nonexistent") == "—"


# ── validate_eligibility ───────────────────────────────────────────────────────

def test_validate_eligibility_passes_for_valid_tier():
    validate_eligibility(MED_TIER, CATALOG)  # should not raise


def test_validate_eligibility_empty_catalog_skips():
    validate_eligibility(MED_TIER, {})  # no-op when catalog missing


def test_validate_eligibility_unknown_provider():
    bad_tier = {
        "name": "med",
        "agents": {"oracle": {"model": "unknown-provider/some-model", "fallback_models": []}},
        "categories": {},
    }
    with pytest.raises(ValueError, match="unknown-provider.*not found"):
        validate_eligibility(bad_tier, CATALOG)


def test_validate_eligibility_unknown_model():
    bad_tier = {
        "name": "med",
        "agents": {"oracle": {"model": "zai/nonexistent-model", "fallback_models": []}},
        "categories": {},
    }
    with pytest.raises(ValueError, match="zai/nonexistent-model.*not listed"):
        validate_eligibility(bad_tier, CATALOG)


def test_validate_eligibility_model_not_eligible_at_tier():
    bad_tier = {
        "name": "free",  # glm-5.1 is NOT eligible at 'free'
        "agents": {"oracle": {"model": "zai/glm-5.1", "fallback_models": []}},
        "categories": {},
    }
    with pytest.raises(ValueError, match="zai/glm-5.1.*not eligible at tier 'free'"):
        validate_eligibility(bad_tier, CATALOG)


def test_validate_eligibility_eligible_string_lists_alternatives():
    bad_tier = {
        "name": "free",
        "agents": {"oracle": {"model": "zai/glm-5.1", "fallback_models": []}},
        "categories": {},
    }
    with pytest.raises(ValueError, match="eligible:"):
        validate_eligibility(bad_tier, CATALOG)


def test_validate_eligibility_checks_fallback_models():
    bad_tier = {
        "name": "free",  # glm-5.1 is not eligible at 'free', even as fallback
        "agents": {"oracle": {"model": "zai/glm-4.7", "fallback_models": ["zai/glm-5.1"]}},
        "categories": {},
    }
    with pytest.raises(ValueError, match="zai/glm-5.1.*not eligible at tier 'free'"):
        validate_eligibility(bad_tier, CATALOG)


# ── load_catalog ──────────────────────────────────────────────────────────────

def test_load_catalog_missing_dir_returns_empty(tmp_path):
    result = load_catalog(tmp_path / "nonexistent")
    assert result == {}


def test_load_catalog_loads_real_providers():
    from pathlib import Path
    providers_dir = Path.home() / ".config" / "opencode" / "providers"
    if not providers_dir.exists():
        pytest.skip("providers/ not found")
    catalog = load_catalog(providers_dir)
    assert "zai" in catalog
    assert "opencode-go" in catalog
    assert "copilot" in catalog
    assert "anthropic" in catalog
    # Each entry has a models block
    for name, cat in catalog.items():
        assert "models" in cat, f"providers/{name}.yaml missing 'models' key"


def test_load_catalog_from_tmp(tmp_path):
    import yaml
    (tmp_path / "myprovider.yaml").write_text(
        yaml.dump({"provider": "myprovider", "quota_unit": "usd_token", "models": {"m1": {"tiers": ["free"]}}})
    )
    catalog = load_catalog(tmp_path)
    assert "myprovider" in catalog
    assert "m1" in catalog["myprovider"]["models"]

"""Tests for pricing module."""

import pytest

from token_tracker.pricing import (
    PRICING_TABLE,
    ModelPricing,
    calculate_cost,
    lookup_pricing,
)


def test_pricing_table_has_known_models():
    assert "claude-sonnet-4-6" in PRICING_TABLE
    assert "claude-opus-4-6" in PRICING_TABLE
    assert "claude-haiku-4-5" in PRICING_TABLE
    assert "glm-5.1" in PRICING_TABLE


def test_pricing_table_free_models():
    free_models = ["glm-5.1", "deepseek-v4-flash", "deepseek-v4-pro", "minimax-m2.7", "big-pickle"]
    for model in free_models:
        p = PRICING_TABLE[model]
        assert p.input_rate == 0
        assert p.output_rate == 0
        assert p.cache_read_rate == 0


def test_calculate_cost_sonnet():
    p = PRICING_TABLE["claude-sonnet-4-6"]
    cost = calculate_cost("claude-sonnet-4-6", 1_000_000, 1_000_000, 500_000)
    expected = 1_000_000 * p.input_rate + 1_000_000 * p.output_rate + 500_000 * p.cache_read_rate
    assert abs(cost - expected) < 0.01


def test_calculate_cost_unknown_model():
    assert calculate_cost("unknown-model", 100, 100, 100) == 0.0


def test_calculate_cost_free_model():
    assert calculate_cost("glm-5.1", 999_999, 999_999, 999_999) == 0.0


def test_lookup_pricing_returns_tuple():
    p = lookup_pricing("claude-opus-4-6")
    assert isinstance(p, ModelPricing)
    assert p.input_rate > 0


def test_lookup_pricing_unknown():
    p = lookup_pricing("does-not-exist")
    assert p.input_rate == 0
    assert p.output_rate == 0
    assert p.cache_read_rate == 0


def test_model_pricing_frozen():
    p = ModelPricing(1e-6, 2e-6, 3e-6)
    with pytest.raises(AttributeError):
        p.input_rate = 99


def test_sonnet_pricing_values():
    p = PRICING_TABLE["claude-sonnet-4-6"]
    assert p.input_rate == 3.00e-6
    assert p.output_rate == 15.00e-6
    assert p.cache_read_rate == 0.30e-6


def test_opus_pricing_values():
    p = PRICING_TABLE["claude-opus-4-6"]
    assert p.input_rate == 15.00e-6
    assert p.output_rate == 75.00e-6
    assert p.cache_read_rate == 1.50e-6


def test_haiku_pricing_values():
    p = PRICING_TABLE["claude-haiku-4-5"]
    assert p.input_rate == 0.80e-6
    assert p.output_rate == 4.00e-6
    assert p.cache_read_rate == 0.08e-6


def test_legacy_model_aliases():
    assert lookup_pricing("claude-3.5-sonnet").input_rate == 3.00e-6
    assert lookup_pricing("claude-3-opus").input_rate == 15.00e-6
    assert lookup_pricing("claude-3-haiku").input_rate == 0.25e-6
"""API pricing tables and cost estimation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class ModelPricing:
    input_rate: float
    output_rate: float
    cache_read_rate: float


PRICING_TABLE: Dict[str, ModelPricing] = {
    "claude-sonnet-4-6": ModelPricing(3.00e-6, 15.00e-6, 0.30e-6),
    "claude-sonnet-4.6": ModelPricing(3.00e-6, 15.00e-6, 0.30e-6),
    "claude-opus-4-6": ModelPricing(15.00e-6, 75.00e-6, 1.50e-6),
    "claude-opus-4.6": ModelPricing(15.00e-6, 75.00e-6, 1.50e-6),
    "claude-haiku-4-5": ModelPricing(0.80e-6, 4.00e-6, 0.08e-6),
    "claude-3.5-sonnet": ModelPricing(3.00e-6, 15.00e-6, 0.30e-6),
    "claude-3-opus": ModelPricing(15.00e-6, 75.00e-6, 1.50e-6),
    "claude-3-haiku": ModelPricing(0.25e-6, 1.25e-6, 0.03e-6),
    "glm-5.1": ModelPricing(0, 0, 0),
    "deepseek-v4-flash": ModelPricing(0, 0, 0),
    "deepseek-v4-pro": ModelPricing(0, 0, 0),
    "minimax-m2.7": ModelPricing(0, 0, 0),
    "big-pickle": ModelPricing(0, 0, 0),
}


def calculate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cache_read_tokens: int = 0,
) -> float:
    p = PRICING_TABLE.get(model)
    if p is None:
        p = ModelPricing(0, 0, 0)
    return round(
        input_tokens * p.input_rate
        + output_tokens * p.output_rate
        + cache_read_tokens * p.cache_read_rate,
        4,
    )


def lookup_pricing(model: str) -> ModelPricing:
    return PRICING_TABLE.get(model, ModelPricing(0, 0, 0))
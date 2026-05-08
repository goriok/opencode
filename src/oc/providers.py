"""Provider catalog — model eligibility, cost mechanics, and resolver.

All functions are pure (no writes). I/O is load_catalog() only.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


# ── Types ──────────────────────────────────────────────────────────────────────

ProviderCatalog = dict[str, Any]   # parsed providers/<name>.yaml


# ── Resolver ──────────────────────────────────────────────────────────────────

def resolve_model(model_str: str) -> tuple[str, str]:
    """Split '<provider>/<model>' → ('provider', 'model').

    Models with no slash are assumed to be 'anthropic' (they reach the stack
    via LiteLLM's anthropic route and are listed in providers/anthropic.yaml).
    """
    if "/" in model_str:
        provider, _, model = model_str.partition("/")
        return provider, model
    return "anthropic", model_str


# ── Loader ────────────────────────────────────────────────────────────────────

def load_catalog(providers_dir: Path) -> dict[str, ProviderCatalog]:
    """Load all provider YAML files from providers_dir.

    Returns a dict keyed by provider name (matches the YAML `provider:` field
    and the filename stem, e.g. 'zai', 'opencode-go', 'copilot').
    Missing directory returns empty dict (catalog is optional — validation
    skipped when catalog not available).
    """
    if not providers_dir.exists():
        return {}
    catalog: dict[str, ProviderCatalog] = {}
    for path in sorted(providers_dir.glob("*.yaml")):
        data = yaml.safe_load(path.read_text())
        if not isinstance(data, dict):
            continue
        name = data.get("provider", path.stem)
        catalog[name] = data
    return catalog


# ── Cost label ────────────────────────────────────────────────────────────────

def cost_label(provider_cat: ProviderCatalog, model_name: str) -> str:
    """Return a human-readable cost string for a model within a provider catalog.

    Examples:
      "2× quota"          (multiplier-based, e.g. zai)
      "10 premium req"    (premium_request, e.g. copilot)
      "$0.50/$2.50 /Mtok" (usd_credit or usd_token, e.g. opencode-go, anthropic)
      "—"                 (model not found in catalog)
    """
    models = provider_cat.get("models", {})
    entry = models.get(model_name)
    if entry is None:
        return "—"

    quota_unit = provider_cat.get("quota_unit", "usd_token")

    if quota_unit == "prompt":
        mult = entry.get("multiplier", 1)
        return f"{mult}× quota"
    if quota_unit == "premium_request":
        mult = entry.get("multiplier", 1)
        label = "premium req" if mult != 1 else "premium req"
        return f"{mult} {label}"
    # usd_credit or usd_token
    in_rate = entry.get("usd_per_mtok_in")
    out_rate = entry.get("usd_per_mtok_out")
    if in_rate is not None and out_rate is not None:
        return f"${in_rate}/${out_rate} /Mtok"
    if in_rate is not None:
        return f"${in_rate} /Mtok in"
    return "—"


# ── Eligibility ───────────────────────────────────────────────────────────────

def _all_models_in_tier(tier: dict[str, Any]) -> list[str]:
    """Collect every model string referenced in a tier (agents + categories + fallbacks)."""
    models: list[str] = []
    for section in ("agents", "categories"):
        for _name, cfg in tier.get(section, {}).items():
            if "model" in cfg:
                models.append(cfg["model"])
            for fb in cfg.get("fallback_models", []):
                models.append(fb)
    return models


def validate_eligibility(
    tier: dict[str, Any],
    catalog: dict[str, ProviderCatalog],
) -> None:
    """Raise ValueError if any model in the tier is ineligible per the catalog.

    Checks three conditions per model string:
    1. The provider exists in catalog (providers/<provider>.yaml loaded).
    2. The model is listed under provider.models.
    3. The tier name is listed in model.tiers.

    No-op when catalog is empty (catalog directory missing → validation skipped).
    """
    if not catalog:
        return

    tier_name = tier.get("name", "<unknown>")
    errors: list[str] = []

    for model_str in _all_models_in_tier(tier):
        provider_name, model_name = resolve_model(model_str)

        if provider_name not in catalog:
            errors.append(
                f"provider '{provider_name}' referenced in tier '{tier_name}' "
                f"but providers/{provider_name}.yaml not found"
            )
            continue

        provider_cat = catalog[provider_name]
        models = provider_cat.get("models", {})

        if model_name not in models:
            errors.append(
                f"{model_str} referenced in tier '{tier_name}' "
                f"but not listed in providers/{provider_name}.yaml"
            )
            continue

        eligible_tiers: list[str] = models[model_name].get("tiers", [])
        if tier_name not in eligible_tiers:
            eligible_str = ", ".join(eligible_tiers) if eligible_tiers else "none"
            errors.append(
                f"{model_str} is not eligible at tier '{tier_name}' "
                f"(eligible: {eligible_str})"
            )

    if errors:
        raise ValueError("\n".join(errors))

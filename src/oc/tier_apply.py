"""Pure render functions for the tier system.

render_plugin(tier, base_plugin) → dict   (new oh-my-openagent content)
render_litellm(tier, base_litellm) → dict  (new litellm/config.yaml content)

Neither function touches the filesystem — all I/O is in commands/tier.py.
"""

from __future__ import annotations

import re
from typing import Any, Optional

from oc.tier_litellm_models import KNOWN_MODELS

# Keys in oh-my-openagent.jsonc that are NOT model assignments; preserve verbatim.
_PASSTHROUGH_KEYS = {
    "disabled_hooks",
    "disabled_agents",
    "disabled_skills",
    "disabled_mcps",
    "runtime_fallback",
    "background_task",
    "experimental",
    "hooks",
    "$schema",
}


def validate_tier(
    tier: dict[str, Any],
    base_plugin: dict[str, Any],
    catalog: Optional[dict] = None,
) -> None:
    """Raise ValueError if tier is incomplete or references ineligible models.

    Two checks are run:
    1. Completeness: every agent/category present in base_plugin must appear in tier.
    2. Eligibility (when catalog is provided): every model referenced must be listed
       in the provider catalog and allowed at this tier.
    """
    from oc.providers import validate_eligibility

    base_agents = set(base_plugin.get("agents", {}).keys())
    base_categories = set(base_plugin.get("categories", {}).keys())
    tier_agents = set(tier.get("agents", {}).keys())
    tier_categories = set(tier.get("categories", {}).keys())

    missing_agents = base_agents - tier_agents
    missing_categories = base_categories - tier_categories

    errors: list[str] = []
    for a in sorted(missing_agents):
        errors.append(f"agent '{a}' present in oh-my-openagent.jsonc but missing from tier '{tier['name']}'")
    for c in sorted(missing_categories):
        errors.append(f"category '{c}' present in oh-my-openagent.jsonc but missing from tier '{tier['name']}'")

    if errors:
        raise ValueError("\n".join(errors))

    if catalog:
        validate_eligibility(tier, catalog)


def _build_agent_entry(agent_cfg: dict[str, Any]) -> dict[str, Any]:
    entry: dict[str, Any] = {"model": agent_cfg["model"]}
    if "thinking" in agent_cfg:
        entry["thinking"] = agent_cfg["thinking"]
    fallback = agent_cfg.get("fallback_models", [])
    if fallback:
        entry["fallback_models"] = fallback
    return entry


def render_plugin(tier: dict[str, Any], base_plugin: dict[str, Any]) -> dict[str, Any]:
    """Build the new oh-my-openagent content dict from a tier definition.

    Passthrough keys (hooks, fallback settings, etc.) are copied from base_plugin.
    agents and categories are fully replaced from the tier.
    """
    result: dict[str, Any] = {}

    # Preserve passthrough keys from base (in their original order where possible).
    for key in base_plugin:
        if key in _PASSTHROUGH_KEYS:
            result[key] = base_plugin[key]

    # Replace routing blocks.
    result["agents"] = {
        name: _build_agent_entry(cfg)
        for name, cfg in tier.get("agents", {}).items()
    }
    result["categories"] = {
        name: _build_agent_entry(cfg)
        for name, cfg in tier.get("categories", {}).items()
    }

    return result


def render_litellm(tier: dict[str, Any], base_litellm: dict[str, Any]) -> dict[str, Any]:
    """Build the new litellm/config.yaml content dict from a tier definition.

    litellm_settings, router_settings, general_settings are preserved from base.
    model_list is rebuilt from the tier's litellm.models list.
    general_settings.max_budget is set if budget.max_usd_month is defined.
    """
    result = dict(base_litellm)

    # Rebuild model_list from tier's litellm.models.
    tier_models: list[str] = tier.get("litellm", {}).get("models", [])
    model_list = []
    for model_name in tier_models:
        if model_name not in KNOWN_MODELS:
            raise ValueError(f"Unknown model '{model_name}' in tier '{tier['name']}' litellm.models — add it to tier_litellm_models.py")
        model_list.append({
            "model_name": model_name,
            "litellm_params": KNOWN_MODELS[model_name],
        })
    result["model_list"] = model_list

    # Apply budget cap to general_settings.
    budget = tier.get("budget", {})
    if "max_usd_month" in budget:
        gs = dict(result.get("general_settings", {}))
        gs["max_budget"] = budget["max_usd_month"]
        result["general_settings"] = gs
    else:
        # Remove any existing max_budget when not set in tier.
        gs = dict(result.get("general_settings", {}))
        gs.pop("max_budget", None)
        result["general_settings"] = gs

    return result


def parse_jsonc(text: str) -> str:
    """Strip // line comments and /* block comments from JSONC before json.loads.

    The resulting string is fed to json.loads(..., strict=False) to handle
    control characters that may appear in schema URLs or other values.
    """
    # Remove block comments first.
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    # Remove line comments (// ...) not inside strings.
    # We track whether we're inside a string to avoid stripping URLs.
    lines = []
    for line in text.splitlines():
        # Only strip // that appear outside of string literals.
        # Approach: find the first unquoted // and trim from there.
        in_string = False
        escape_next = False
        comment_pos = None
        for i, ch in enumerate(line):
            if escape_next:
                escape_next = False
                continue
            if ch == "\\" and in_string:
                escape_next = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if not in_string and ch == "/" and i + 1 < len(line) and line[i + 1] == "/":
                comment_pos = i
                break
        if comment_pos is not None:
            lines.append(line[:comment_pos].rstrip())
        else:
            lines.append(line)
    return "\n".join(lines)


def loads_jsonc(text: str) -> dict:
    """Parse a JSONC string, tolerating control characters (e.g. in schema URLs)."""
    import json
    return json.loads(parse_jsonc(text), strict=False)

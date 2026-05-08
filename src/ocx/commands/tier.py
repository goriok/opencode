"""oc tier — manage model-budget tier profiles."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Annotated, Optional

import typer
import yaml
from rich.console import Console
from rich.table import Table

from ocx import log
from ocx.paths import LITELLM_CONFIG, OH_MY_OPENAGENT, PROVIDERS_DIR, TIER_STATE, TIERS_DIR
from ocx.providers import cost_label, load_catalog, resolve_model
from ocx.tier_apply import loads_jsonc, render_litellm, render_plugin, validate_tier

app = typer.Typer(help="Manage model-budget tier profiles (free/low/med/high/max).")

_console = Console()

TIER_ORDER = ["free", "low", "med", "high", "max"]


# ── helpers ────────────────────────────────────────────────────────────────────

def _load_tier(name: str) -> dict:
    path = TIERS_DIR / f"{name}.yaml"
    if not path.exists():
        log.error(f"tier '{name}' not found — expected {path}")
    return yaml.safe_load(path.read_text())


def _load_base_plugin() -> dict:
    if not OH_MY_OPENAGENT.exists():
        log.error(f"oh-my-openagent.jsonc not found at {OH_MY_OPENAGENT}")
    return loads_jsonc(OH_MY_OPENAGENT.read_text())


def _load_base_litellm() -> dict:
    if not LITELLM_CONFIG.exists():
        log.error(f"litellm/config.yaml not found at {LITELLM_CONFIG}")
    return yaml.safe_load(LITELLM_CONFIG.read_text())


def _current_tier() -> Optional[str]:
    if TIER_STATE.exists():
        state = json.loads(TIER_STATE.read_text())
        return state.get("active")
    return None


def _write_state(name: str) -> None:
    state = {"active": name, "applied_at": datetime.now(timezone.utc).isoformat()}
    TIER_STATE.write_text(json.dumps(state, indent=2))


def _available_tiers() -> list[str]:
    if not TIERS_DIR.exists():
        return []
    names = [p.stem for p in sorted(TIERS_DIR.glob("*.yaml"))]
    # Sort by canonical order, unknown tiers appended alphabetically.
    ordered = [n for n in TIER_ORDER if n in names]
    extras = sorted(n for n in names if n not in TIER_ORDER)
    return ordered + extras


def _load_catalog() -> dict:
    return load_catalog(PROVIDERS_DIR)


def _budget_str(tier: dict) -> str:
    usd = tier.get("budget", {}).get("max_usd_month")
    if usd is None:
        return "—"
    if usd == 0:
        return "free"
    return f"${usd}/mo"


def _mode_str(tier: dict) -> str:
    providers = tier.get("providers_used", [])
    if len(providers) == 1:
        return f"solo:{providers[0]}"
    if len(providers) > 1:
        return "blended"
    return "?"


def _plugin_diff_rows(tier_a: dict, tier_b: dict, base_plugin: dict) -> list[tuple[str, str, str, str]]:
    """Return (type, name, from_model, to_model) rows where the two tiers differ."""
    rendered_a = render_plugin(tier_a, base_plugin)
    rendered_b = render_plugin(tier_b, base_plugin)
    rows: list[tuple[str, str, str, str]] = []
    for section, label in (("agents", "agent"), ("categories", "category")):
        for name in rendered_a.get(section, {}):
            model_a = rendered_a[section][name]["model"]
            model_b = rendered_b[section].get(name, {}).get("model", "—")
            if model_a != model_b:
                rows.append((label, name, model_a, model_b))
    return rows


# ── subcommands ────────────────────────────────────────────────────────────────

@app.command(name="list")
def tier_list() -> None:
    """List all available tier profiles."""
    tiers = _available_tiers()
    current = _current_tier()

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("", width=2)
    table.add_column("Tier", style="bold")
    table.add_column("Budget")
    table.add_column("Mode")
    table.add_column("Description")

    for name in tiers:
        tier = _load_tier(name)
        marker = "▶" if name == current else ""
        table.add_row(marker, name, _budget_str(tier), _mode_str(tier), tier.get("description", ""))

    _console.print(table)
    if current is None:
        _console.print("[yellow]No tier currently active. Run: oc tier set <name>[/yellow]")


@app.command()
def show(name: str) -> None:
    """Print the full model assignments for a tier."""
    tier = _load_tier(name)
    base = _load_base_plugin()
    rendered = render_plugin(tier, base)
    catalog = _load_catalog()

    _console.print(f"\n[bold cyan]{name}[/bold cyan] — {tier.get('description', '')}")
    _console.print(f"Budget: [green]{_budget_str(tier)}[/green]  Mode: {_mode_str(tier)}")

    table = Table(show_header=True, header_style="bold")
    table.add_column("Type", style="dim")
    table.add_column("Name")
    table.add_column("Model")
    table.add_column("Cost")
    table.add_column("Fallback(s)")

    for agent_name, cfg in rendered.get("agents", {}).items():
        fallback = ", ".join(cfg.get("fallback_models", [])) or "—"
        model_str = cfg["model"]
        provider_name, model_name = resolve_model(model_str)
        provider_cat = catalog.get(provider_name, {})
        clabel = cost_label(provider_cat, model_name) if provider_cat else "—"
        table.add_row("agent", agent_name, model_str, clabel, fallback)
    for cat_name, cfg in rendered.get("categories", {}).items():
        fallback = ", ".join(cfg.get("fallback_models", [])) or "—"
        model_str = cfg["model"]
        provider_name, model_name = resolve_model(model_str)
        provider_cat = catalog.get(provider_name, {})
        clabel = cost_label(provider_cat, model_name) if provider_cat else "—"
        table.add_row("category", cat_name, model_str, clabel, fallback)

    _console.print(table)

    litellm_models = tier.get("litellm", {}).get("models", [])
    if litellm_models:
        _console.print(f"\nLiteLLM proxied models: {', '.join(litellm_models)}")
    else:
        _console.print("\nLiteLLM proxied models: none")


@app.command()
def current() -> None:
    """Print the active tier name."""
    name = _current_tier()
    if name:
        _console.print(name)
    else:
        _console.print("[yellow]No tier active.[/yellow]")
        raise typer.Exit(1)


@app.command()
def diff(tier_a: str, tier_b: str) -> None:
    """Show model-assignment differences between two tiers."""
    a = _load_tier(tier_a)
    b = _load_tier(tier_b)
    base = _load_base_plugin()

    try:
        validate_tier(a, base)
        validate_tier(b, base)
    except ValueError as exc:
        log.error(str(exc))

    rows = _plugin_diff_rows(a, b, base)
    if not rows:
        _console.print(f"[green]Tiers '{tier_a}' and '{tier_b}' have identical model assignments.[/green]")
        return

    _console.print(f"\n[bold]Diff:[/bold] {tier_a} → {tier_b}\n")
    table = Table(show_header=True, header_style="bold")
    table.add_column("Type", style="dim")
    table.add_column("Name")
    table.add_column(f"From ({tier_a})", style="red")
    table.add_column(f"To ({tier_b})", style="green")
    for label, name, from_model, to_model in rows:
        table.add_row(label, name, from_model, to_model)
    _console.print(table)


@app.command(name="set")
def tier_set(
    name: str,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Show what would change without writing.")] = False,
) -> None:
    """Apply a tier: rewrite oh-my-openagent.jsonc and litellm/config.yaml."""
    tier = _load_tier(name)
    base_plugin = _load_base_plugin()
    base_litellm = _load_base_litellm()
    catalog = _load_catalog()

    # Validate completeness + eligibility.
    try:
        validate_tier(tier, base_plugin, catalog=catalog)
    except ValueError as exc:
        log.error(str(exc))

    # Render new content.
    new_plugin = render_plugin(tier, base_plugin)
    new_litellm = render_litellm(tier, base_litellm)

    if dry_run:
        log.section(f"Dry-run: tier '{name}'")
        _console.print("\n[bold]oh-my-openagent.jsonc agents:[/bold]")
        for agent_name, cfg in new_plugin["agents"].items():
            _console.print(f"  {agent_name:<22} {cfg['model']}")
        _console.print("\n[bold]oh-my-openagent.jsonc categories:[/bold]")
        for cat_name, cfg in new_plugin["categories"].items():
            _console.print(f"  {cat_name:<22} {cfg['model']}")
        _console.print(f"\n[bold]litellm/config.yaml model_list:[/bold]")
        for entry in new_litellm["model_list"]:
            _console.print(f"  {entry['model_name']}")
        budget = tier.get("budget", {}).get("max_usd_month")
        if budget is not None:
            _console.print(f"\n[bold]general_settings.max_budget:[/bold] {budget}")
        return

    # Write oh-my-openagent.jsonc.
    plugin_json = json.dumps(new_plugin, indent=2, ensure_ascii=False)
    OH_MY_OPENAGENT.write_text(plugin_json + "\n")
    log.info(f"wrote oh-my-openagent.jsonc (tier: {name})")

    # Write litellm/config.yaml.
    litellm_yaml = yaml.dump(new_litellm, default_flow_style=False, allow_unicode=True, sort_keys=False)
    LITELLM_CONFIG.write_text(litellm_yaml)
    log.info(f"wrote litellm/config.yaml (tier: {name})", prefix="litellm")

    # Save state.
    _write_state(name)

    budget_str = _budget_str(tier)
    _console.print(f"\n[green]✓ Tier '{name}' applied[/green] (budget: {budget_str})")
    _console.print("[dim]Restart proxy to apply: oc litellm down && oc litellm up[/dim]")

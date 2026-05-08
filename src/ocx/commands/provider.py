"""oc provider — inspect provider catalogs (eligibility, cost mechanics)."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from ocx import log
from ocx.paths import PROVIDERS_DIR
from ocx.providers import cost_label, load_catalog

app = typer.Typer(help="Inspect provider model catalogs (eligibility, cost mechanics).")

_console = Console()


def _load() -> dict:
    catalog = load_catalog(PROVIDERS_DIR)
    if not catalog:
        log.error(f"No provider catalogs found at {PROVIDERS_DIR}. Create providers/*.yaml files.")
    return catalog


@app.command(name="list")
def provider_list() -> None:
    """List all provider catalogs with quota unit and model count."""
    catalog = _load()

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Provider", style="bold")
    table.add_column("Quota unit")
    table.add_column("Models")
    table.add_column("Description")

    for name, cat in catalog.items():
        quota_unit = cat.get("quota_unit", "?")
        model_count = str(len(cat.get("models", {})))
        desc = cat.get("description", "").strip().replace("\n", " ")
        if len(desc) > 60:
            desc = desc[:57] + "..."
        table.add_row(name, quota_unit, model_count, desc)

    _console.print(table)


@app.command()
def show(name: str) -> None:
    """Print full model catalog for a provider: cost mechanics, eligible tiers, flags."""
    catalog = _load()

    if name not in catalog:
        available = ", ".join(sorted(catalog.keys()))
        log.error(f"Provider '{name}' not found. Available: {available}")

    cat = catalog[name]
    quota_unit = cat.get("quota_unit", "?")
    desc = cat.get("description", "").strip()

    _console.print(f"\n[bold cyan]{name}[/bold cyan] — quota unit: [green]{quota_unit}[/green]")
    if desc:
        _console.print(f"[dim]{desc}[/dim]\n")

    sub = cat.get("subscription_tiers", {})
    if sub:
        _console.print("[bold]Subscription plans:[/bold]")
        for plan_name, plan_info in sub.items():
            parts = [f"{k}: {v}" for k, v in plan_info.items()]
            _console.print(f"  {plan_name}: {', '.join(parts)}")
        _console.print()

    models = cat.get("models", {})
    if not models:
        _console.print("[yellow]No models defined.[/yellow]")
        return

    table = Table(show_header=True, header_style="bold")
    table.add_column("Model")
    table.add_column("Cost")
    table.add_column("Flags")
    table.add_column("Eligible tiers")

    for model_name, entry in models.items():
        clabel = cost_label(cat, model_name)
        flags: list[str] = []
        if entry.get("thinking_capable"):
            flags.append("thinking")
        if entry.get("multimodal"):
            flags.append("multimodal")
        ctx = entry.get("context_k")
        if ctx:
            flags.append(f"{ctx}K ctx")
        eligible = entry.get("tiers", [])
        table.add_row(
            model_name,
            clabel,
            ", ".join(flags) or "—",
            ", ".join(eligible) or "—",
        )

    _console.print(table)

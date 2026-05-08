import typer

from ocx.paths import OPENCODE_CONFIGS, OPENCODE_DIR

app = typer.Typer(help="Check opencode configuration files.")


@app.command()
def check() -> None:
    """List opencode config files and whether they exist."""
    typer.echo("[opencode] Configuration files:")
    for name in OPENCODE_CONFIGS:
        path = OPENCODE_DIR / name
        mark = "✅" if path.exists() else "❌"
        suffix = "" if path.exists() else " (missing)"
        typer.echo(f"  {mark} {name}{suffix}")

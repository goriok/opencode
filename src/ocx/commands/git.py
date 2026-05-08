import subprocess

import typer

from ocx import log
from ocx.paths import OPENCODE_DIR

app = typer.Typer(help="Git helpers for the opencode config repo.")


@app.command()
def status() -> None:
    """Show git status of the opencode config repo."""
    log.info("Git status:")
    subprocess.run(["git", "status", "--short"], cwd=OPENCODE_DIR)

    typer.echo("")
    typer.echo("Tracked primary agents:")
    result = subprocess.run(
        ["git", "ls-files", "agents/*.md"],
        cwd=OPENCODE_DIR,
        capture_output=True,
        text=True,
    )
    tracked = result.stdout.strip()
    typer.echo(tracked if tracked else "  (none tracked)")

    typer.echo("")
    typer.echo("Modified tracked files:")
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=OPENCODE_DIR,
        capture_output=True,
        text=True,
    )
    modified = result.stdout.strip()
    typer.echo(modified if modified else "  (clean)")

import os
import shutil
from pathlib import Path

import typer

from ocx import log

app = typer.Typer(help="Manage shell shortcuts (oc, ocw, ocwserve).")

_MARKER = "# OpenCode Shortcuts"

_ZSH_BASH_BLOCK = """
# OpenCode Shortcuts
alias oc="opencode"
alias ocw="opencode web"

ocwserve() {
  local port="${1:-4096}"
  local host="${2:-0.0.0.0}"
  opencode web --port "$port" --hostname "$host"
}
"""

_FISH_BLOCK = """
# OpenCode Shortcuts
alias oc "opencode"
alias ocw "opencode web"

function ocwserve
  set port (test -n "$argv[1]"; and echo "$argv[1]"; or echo "4096")
  set host (test -n "$argv[2]"; and echo "$argv[2]"; or echo "0.0.0.0")
  opencode web --port "$port" --hostname "$host"
end
"""


def _detect_shell() -> str:
    if os.environ.get("ZSH_VERSION"):
        return "zsh"
    if os.environ.get("BASH_VERSION"):
        return "bash"
    if shutil.which("fish"):
        return "fish"
    return "zsh"


def _install_to(config_file: Path, block: str, shell_name: str) -> None:
    config_file.parent.mkdir(parents=True, exist_ok=True)
    if not config_file.exists():
        config_file.touch()

    if _MARKER in config_file.read_text(encoding="utf-8"):
        log.warn(f"Shortcuts already exist in {config_file}")
        return

    with config_file.open("a", encoding="utf-8") as f:
        f.write(block)
    log.info(f"Shortcuts installed in {config_file}")


@app.command()
def install(
    shell: str = typer.Option(None, "--shell", help="Shell type: zsh, bash, or fish (auto-detected if omitted)"),
) -> None:
    """Install shell aliases (oc, ocw, ocwserve) into your shell config."""
    shell_type = shell or _detect_shell()
    log.info(f"Installing shortcuts for shell: {shell_type}")

    home = Path.home()
    if shell_type == "zsh":
        _install_to(home / ".zshrc", _ZSH_BASH_BLOCK, "zsh")
    elif shell_type == "bash":
        _install_to(home / ".bashrc", _ZSH_BASH_BLOCK, "bash")
    elif shell_type == "fish":
        _install_to(home / ".config" / "fish" / "config.fish", _FISH_BLOCK, "fish")
    else:
        log.error(f"Unsupported shell: {shell_type}. Choose zsh, bash, or fish.")
        raise typer.Exit(1)

    typer.echo("")
    typer.echo("Usage:")
    typer.echo("  oc              — Opens OpenCode TUI")
    typer.echo("  ocw             — Opens OpenCode Web (random port)")
    typer.echo("  ocwserve 4096   — Opens Web on port 4096")
    typer.echo("  ocwserve 4096 127.0.0.1 — Web local only")
    typer.echo("")
    typer.echo(f"To apply now: source ~/.{shell_type}rc" if shell_type != "fish" else "To apply now: source ~/.config/fish/config.fish")

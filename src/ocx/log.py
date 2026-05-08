import sys
import typer
from rich.console import Console

_console = Console()
_err_console = Console(stderr=True)


def info(msg: str, prefix: str = "opencode") -> None:
    _console.print(f"[green]\\[{prefix}][/green] {msg}")


def warn(msg: str, prefix: str = "opencode") -> None:
    _console.print(f"[yellow]\\[{prefix}][/yellow] {msg}")


def error(msg: str, prefix: str = "opencode") -> None:
    _err_console.print(f"[red]\\[{prefix}][/red] {msg}")
    raise typer.Exit(1)


def section(msg: str) -> None:
    _console.rule(f"[cyan]{msg}[/cyan]")
    _console.print()

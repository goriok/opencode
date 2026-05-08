import typer

from oc.commands import agents, configs, git, litellm, setup, shortcuts

app = typer.Typer(
    name="oc",
    help="opencode config CLI — manage agents, LiteLLM proxy, shortcuts, and more.",
    no_args_is_help=True,
)

app.add_typer(agents.app, name="agents")
app.add_typer(litellm.app, name="litellm")
app.add_typer(shortcuts.app, name="shortcuts")
app.add_typer(configs.app, name="configs")
app.add_typer(git.app, name="git")


@app.command(name="setup")
def setup_cmd() -> None:
    """Full machine setup: clone agency-agents, install, sync to Claude Code."""
    setup.run_setup()

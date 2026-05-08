import tempfile
from pathlib import Path

import typer

from oc import log, proc
from oc.paths import AGENCY_AGENTS_REPO, AGENTS_DIR, LITELLM_DIR

app = typer.Typer(help="Full machine setup.")


def run_setup() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_repo = Path(tmp) / "agency-agents"
        log.info("Cloning agency-agents (shallow)...")
        proc.run(["git", "clone", "--depth=1", AGENCY_AGENTS_REPO, str(tmp_repo)])

        log.info("Converting agents for opencode format...")
        proc.run(["bash", str(tmp_repo / "scripts" / "convert.sh"), "--tool", "opencode"])

        AGENTS_DIR.mkdir(parents=True, exist_ok=True)

        import shutil
        src_agents = tmp_repo / "integrations" / "opencode" / "agents"
        for md in src_agents.glob("*.md"):
            shutil.copy2(md, AGENTS_DIR / md.name)

        count = len(list(AGENTS_DIR.glob("*.md")))
        log.info(f"Done! {count} agents installed to {AGENTS_DIR}")

    log.info("Syncing primary agents to Claude Code...")
    from oc.commands.agents import sync
    sync()

    setup_litellm_sh = LITELLM_DIR / "setup-litellm.sh"
    if setup_litellm_sh.exists():
        setup_litellm_sh.chmod(setup_litellm_sh.stat().st_mode | 0o111)


@app.callback(invoke_without_command=True)
def setup(ctx: typer.Context) -> None:
    """Full machine setup: clone agency-agents, install, sync to Claude Code."""
    if ctx.invoked_subcommand is None:
        run_setup()

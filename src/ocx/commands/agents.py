import re
import tempfile
from pathlib import Path

import typer

from ocx import log, proc
from ocx.paths import (
    AGENCY_AGENTS_REPO,
    AGENTS_DIR,
    CLAUDE_AGENTS_DIR,
    OPENCODE_DIR,
    PRIMARY_AGENTS,
)

app = typer.Typer(help="Manage opencode agents.")


def _strip_opencode_frontmatter(text: str) -> str:
    """Remove `mode:` and `permission:` blocks from YAML front matter.

    Mirrors the awk logic in sync-primary-agents.sh lines 54-65.
    Only touches content between the first pair of `---` delimiters.
    """
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip() != "---":
        return text

    result: list[str] = [lines[0]]
    i = 1
    in_permission = False
    frontmatter_done = False

    while i < len(lines):
        line = lines[i]
        stripped = line.rstrip()

        if not frontmatter_done and stripped == "---":
            frontmatter_done = True
            in_permission = False
            result.append(line)
            i += 1
            break

        if not frontmatter_done:
            if re.match(r"^mode:", line):
                i += 1
                continue
            if re.match(r"^permission:", line):
                in_permission = True
                i += 1
                continue
            if in_permission and re.match(r"^  ", line):
                i += 1
                continue
            if in_permission:
                in_permission = False
            result.append(line)
            i += 1
            continue

        result.append(line)
        i += 1

    # append remaining lines (body after frontmatter)
    result.extend(lines[i:])
    return "".join(result)


@app.command()
def sync() -> None:
    """Sync primary agents from opencode to ~/.claude/agents/ (stripping opencode-only frontmatter)."""
    CLAUDE_AGENTS_DIR.mkdir(parents=True, exist_ok=True)

    synced = 0
    for agent_name in PRIMARY_AGENTS:
        src = AGENTS_DIR / agent_name
        dst = CLAUDE_AGENTS_DIR / agent_name

        if not src.exists():
            log.warn(f"Skipping {agent_name} — not found at {src}")
            continue

        content = src.read_text(encoding="utf-8")
        stripped = _strip_opencode_frontmatter(content)
        dst.write_text(stripped, encoding="utf-8")
        log.info(f"Synced: {agent_name} → {dst}")
        synced += 1

    log.info(f"Done — {synced} primary agent(s) synced to {CLAUDE_AGENTS_DIR}")
    log.info("Claude Code will load them automatically from ~/.claude/agents/")


@app.command()
def install(
    path: Path = typer.Argument(None, help="Target project directory (default: cwd)"),
) -> None:
    """Install agency-agents into a project directory."""
    target = path or Path.cwd()
    agents_dir = target / ".opencode" / "agents"

    if agents_dir.exists():
        log.warn(f"Agents already installed at {agents_dir}")
        log.warn(f"Remove the directory to reinstall: rm -rf {agents_dir}")
        raise typer.Exit(0)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_repo = Path(tmp) / "agency-agents"
        log.info("Cloning agency-agents (shallow)...")
        proc.run(["git", "clone", "--depth=1", AGENCY_AGENTS_REPO, str(tmp_repo)])

        log.info("Converting agents for opencode format...")
        proc.run(["bash", str(tmp_repo / "scripts" / "convert.sh"), "--tool", "opencode"])

        log.info(f"Installing agents to {agents_dir}...")
        proc.stream(
            ["bash", str(tmp_repo / "scripts" / "install.sh"), "--tool", "opencode", "--no-interactive"],
            cwd=target,
        )

    count = len(list(agents_dir.glob("*.md"))) if agents_dir.exists() else 0
    log.info(f"Done! {count} agents installed to {agents_dir}")


@app.command()
def count() -> None:
    """Show count of installed agent files in ~/.config/opencode/agents/."""
    count = len(list(AGENTS_DIR.glob("*.md"))) if AGENTS_DIR.exists() else 0
    log.info(f"{count} agents installed in {AGENTS_DIR}")


@app.command()
def update() -> None:
    """Re-clone agency-agents and reinstall (full refresh). Alias for `oc setup`."""
    from ocx.commands.setup import run_setup
    run_setup()

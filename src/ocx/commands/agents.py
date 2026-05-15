import hashlib
import re
import shutil
import tempfile
from pathlib import Path

import typer

from ocx import log, proc
from ocx.paths import (
    AGENCY_AGENTS_REPO,
    AGENTS_DIR,
    CLAUDE_AGENTS_DIR,
    CLAUDE_SKILLS_DIR,
    OPENCODE_DIR,
    PRIMARY_AGENTS,
    SKILLS_DIR,
)

app = typer.Typer(help="Manage opencode agents.")

SYNC_HEADER_TEMPLATE = """\
<!--
  AUTO-SYNCED from {source}
  DO NOT EDIT — overwritten on next `ocx agents sync`.
  Source of truth: {source}
-->
"""

# Transformations applied when syncing shared skills to Claude Code.
# Each entry is (opencode_pattern, claude_replacement) as regex/string pairs.
_SKILL_TRANSFORMS: list[tuple[str, str]] = [
    (r"\bTask tool\b", "Agent tool"),
    (r"\bvia the Task tool\b", "via the Agent tool"),
    (r"\bspawning a subagent via the Task tool\b", "spawning a subagent via the Agent tool"),
    (r"\bspawn a subagent via the Task tool\b", "spawn a subagent via the Agent tool"),
    (r"`show_options` tool", "`AskUserQuestion` tool"),
    (r"`show_options`", "`AskUserQuestion`"),
]


def _strip_opencode_frontmatter(text: str) -> str:
    """Remove `mode:` and `permission:` blocks from YAML front matter."""
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

    result.extend(lines[i:])
    return "".join(result)


def _read_frontmatter_field(text: str, field: str) -> str | None:
    """Extract a single scalar field from YAML frontmatter. Returns None if not found."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        m = re.match(rf"^{re.escape(field)}:\s*(.+)$", line)
        if m:
            return m.group(1).strip().strip('"').strip("'")
    return None


def _transform_for_claude(text: str, source_path: Path) -> str:
    """Apply Claude Code-specific transformations to a skill's content.

    Skips blocks delimited by <!-- skip-sync --> ... <!-- /skip-sync -->.
    Inserts an AUTO-SYNCED header after the frontmatter closing ---.
    """
    # Split into skip-sync protected segments
    skip_pattern = re.compile(
        r"(<!--\s*skip-sync\s*-->.*?<!--\s*/skip-sync\s*-->)", re.DOTALL
    )
    segments = skip_pattern.split(text)

    transformed_segments = []
    for i, seg in enumerate(segments):
        if i % 2 == 1:
            # Inside skip-sync block — preserve as-is
            transformed_segments.append(seg)
        else:
            result = seg
            for pattern, replacement in _SKILL_TRANSFORMS:
                result = re.sub(pattern, replacement, result)
            transformed_segments.append(result)

    transformed = "".join(transformed_segments)

    # Insert AUTO-SYNCED header after the frontmatter closing ---
    rel = source_path.relative_to(Path.home())
    header = SYNC_HEADER_TEMPLATE.format(source=f"~/{rel}")
    fm_close = re.search(r"^---\s*$", transformed, re.MULTILINE)
    if fm_close:
        insert_at = fm_close.end()
        transformed = transformed[:insert_at] + "\n" + header + transformed[insert_at:]
    else:
        transformed = header + transformed

    return transformed


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _expected_hash(src_skill_dir: Path, dst_skill_file: Path) -> str:
    """Hash of what the sync would produce for a given skill file."""
    src_file = src_skill_dir / dst_skill_file.name
    if not src_file.exists():
        return ""
    content = src_file.read_text(encoding="utf-8")
    tool_tag = _read_frontmatter_field(content, "tool") or "shared"
    if tool_tag == "claude-only":
        transformed = content
    else:
        transformed = _transform_for_claude(content, src_file)
    return hashlib.sha256(transformed.encode()).hexdigest()


@app.command()
def sync(
    check: bool = typer.Option(False, "--check", help="Check for drift without writing."),
) -> None:
    """Sync primary agents and shared/claude-only skills to ~/.claude/.

    With --check: report drift and exit 1 if any file diverges from source.
    """
    _sync_agents()
    _sync_skills(check=check)


def _sync_agents() -> None:
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
        log.info(f"Synced agent: {agent_name} → {dst}")
        synced += 1
    log.info(f"Done — {synced} primary agent(s) synced to {CLAUDE_AGENTS_DIR}")


def _sync_skills(check: bool = False) -> None:
    if not SKILLS_DIR.exists():
        log.warn(f"Skills directory not found: {SKILLS_DIR}")
        return

    CLAUDE_SKILLS_DIR.mkdir(parents=True, exist_ok=True)

    drifted: list[str] = []
    synced = skipped = 0

    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir():
            continue

        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue

        content = skill_file.read_text(encoding="utf-8")
        tool_tag = _read_frontmatter_field(content, "tool") or "shared"

        if tool_tag == "opencode-only":
            skipped += 1
            continue

        # Both shared and claude-only go to ~/.claude/skills/
        dst_dir = CLAUDE_SKILLS_DIR / skill_dir.name
        dst_file = dst_dir / "SKILL.md"

        if tool_tag == "claude-only":
            transformed = content  # no transformation — already Claude dialect
        else:
            transformed = _transform_for_claude(content, skill_file)

        if check:
            if dst_file.exists():
                actual_hash = _file_hash(dst_file)
                expected_hash = hashlib.sha256(transformed.encode()).hexdigest()
                if actual_hash != expected_hash:
                    drifted.append(skill_dir.name)
            else:
                drifted.append(f"{skill_dir.name} (missing)")
            continue

        dst_dir.mkdir(parents=True, exist_ok=True)

        # Copy all files in the skill dir, transform only SKILL.md
        for src_file in skill_dir.iterdir():
            dst_f = dst_dir / src_file.name
            if src_file.name == "SKILL.md":
                dst_f.write_text(transformed, encoding="utf-8")
            elif src_file.is_file():
                shutil.copy2(src_file, dst_f)

        log.info(f"Synced skill [{tool_tag}]: {skill_dir.name} → {dst_dir}")
        synced += 1

    if check:
        if drifted:
            log.warn(f"Drift detected in {len(drifted)} skill(s):")
            for name in drifted:
                log.warn(f"  - {name}")
            raise typer.Exit(1)
        else:
            log.info("No drift detected — all skills match source.")
        return

    log.info(
        f"Done — {synced} skill(s) synced, {skipped} opencode-only skipped → {CLAUDE_SKILLS_DIR}"
    )


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

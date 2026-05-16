@AGENTS.md

# opencode-config — Claude Code

## Important Constraints

- IMPORTANT: `agents/` IS tracked in git (84 files). Do not treat it as gitignored.
- IMPORTANT: After editing any primary agent file, run `ocx agents sync` to mirror to `~/.claude/agents/`
- IMPORTANT: Do NOT edit `~/.claude/agents/*.md` or `~/.claude/skills/*.md` directly — they are generated mirrors
- IMPORTANT: The config file is `opencode.jsonc` (`.jsonc` extension), not `opencode.json`
- IMPORTANT: `maestro.md` does not exist — use `agents-orchestrator.md`

## Python CLI Style (enforced)

```python
# Correct — use module helpers
log.info("message")          # not print()
proc.run(["cmd"])            # not os.system() or subprocess directly
AGENTS_DIR / "file.md"      # not Path("~/.config/opencode/agents/file.md")
```

## Test Before Claiming Done

```bash
uv run pytest                # must pass before any fix is complete
ocx agents sync --check      # must pass after any agent/skill edit
```

## References

- CLI source: `src/ocx/`
- Tier profiles: `tiers/<name>.yaml`
- Skills: `skills/*/SKILL.md`
- Primary agents: `agents/alan-turing.md`, `agents/grace-hopper.md`, `agents/tony-hoare.md`, `agents/ada-lovelace.md`, `agents/margaret-hamilton.md`

---
name: init-repo-docs
description: Generate README.md, CONTRIBUTING.md, CLAUDE.md, and AGENTS.md for a new or existing repository following 2025 best practices for AI-era projects.
disable-model-invocation: true
argument-hint: [project-name]
tool: shared
---

# Init Repo Docs

Generate the four canonical documentation files for an AI-era repository. Run this once per project at the repository root.

## Files Generated

| File | Audience | Purpose |
|------|----------|---------|
| `README.md` | Humans (users, contributors) | What, why, quick-start, architecture |
| `CONTRIBUTING.md` | Humans (contributors) | PR process, code style, legal, setup |
| `AGENTS.md` | All AI coding agents | Machine-readable canonical operational context |
| `CLAUDE.md` | Claude Code CLI | Imports `@AGENTS.md` + Claude-specific overrides |

## Canonical Source: AGENTS.md

**AGENTS.md is always the canonical source. CLAUDE.md is a Claude adapter over it.**

Why AGENTS.md, not CLAUDE.md:

1. **AGENTS.md has no import mechanism** — no `@file` syntax exists. It must be complete and self-contained. Making it a wrapper around something else is architecturally impossible.

2. **Tool support is asymmetric:**

   | File | Read natively by |
   |------|-----------------|
   | `AGENTS.md` | Codex, Copilot, Cursor, Windsurf, OpenCode (5+ tools) |
   | `CLAUDE.md` | Claude Code only |

3. **Anthropic's own docs mandate this pattern:**
   ```markdown
   # CLAUDE.md
   @AGENTS.md

   ## Claude Code-specific
   Use plan mode for all changes under src/billing/.
   ```

4. **Symlink direction** (when content is identical): `ln -s AGENTS.md CLAUDE.md` — never the reverse. Symlinking AGENTS.md to CLAUDE.md would pollute all non-Claude tools with Claude-specific directives.

## Workflow

1. **Gather context** — Read `package.json`, `pyproject.toml`, `Cargo.toml`, `.nvmrc`, `docker-compose.yml`, or any config files that reveal the tech stack, scripts, and tooling. Run `git log --oneline -20` to understand project history.
2. **Detect existing files** — Check which of the four files already exist. Never overwrite without asking; offer to merge or update instead.
3. **Generate AGENTS.md first** — it is the canonical source used by all other tools.
4. **Generate README.md** — full human-readable overview.
5. **Generate CONTRIBUTING.md** — contribution guide with legal, setup, and process.
6. **Generate CLAUDE.md** — first line is `@AGENTS.md`, then Claude-specific additions only.

## README.md Rules

### Required Sections (in order)

```
# Project Name
[CI badge] [version badge] [license badge]
One-sentence tagline

## Overview
## Quick Start
## Features
## Architecture
## Configuration
## Usage
## Project Structure   (for complex projects)
## Contributing
## License
```

### Rules
- Badge row: max 8 badges, single row, use shields.io
- **Quick Start** must be copy-paste executable top to bottom with zero prior knowledge
- Prerequisites list exact versions: `Python 3.11+`, `Node.js 20+`
- Include a Mermaid diagram for agent flow or data pipeline — GitHub renders it natively
- Configuration: table with columns `Variable | Description | Required | Default | Example`
- State the AI/agent pattern explicitly: RAG, ReAct, tool-calling, multi-agent, etc.
- State which model version was tested against and what context window is assumed
- Use standard heading names (`## Installation`, `## Configuration`) for AI tool discoverability
- Never duplicate the full CONTRIBUTING.md content — one paragraph + link
- License: one line only

### Anti-patterns
- Wall of badges (>8, multi-row)
- GIF demos without text fallback
- "Coming soon" sections without dates
- Inline API reference (link to docs instead)

## CONTRIBUTING.md Rules

### Required Sections (in order)

```
## Welcome & Scope
## Code of Conduct
## Legal (DCO or CLA)
## Development Setup
## Common Commands
## Commit Convention
## Branching Strategy
## Pull Request Process
## Testing Requirements
## Code Style & Linting
## Reporting Bugs & Security
## Feature Requests
## Prompt & Model Change Policy  (AI-era projects)
```

### Rules
- **DCO by default** for open-source: `git commit -s` with one-line explanation of what DCO means
- **CLA** for corporate projects: link to CLA Assistant
- Development setup: prerequisites with exact versions, copy-paste commands including env var setup
- Commit convention: mandate Conventional Commits (`feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `ci`)
- For AI projects add `model` scope: `feat(model): switch default to claude-sonnet-4-6`
- PR process: require linked issue for non-trivial PRs, state review SLA (e.g., 7 business days)
- Testing: gate real-LLM integration tests behind `@pytest.mark.integration`, not run in default CI
- Security: NEVER public issues — provide `security@domain.com` or GitHub private advisory link
- AI-era extra: PRs modifying prompts/tool definitions must include before/after example runs

## AGENTS.md Rules

### Why AGENTS.md is canonical
- AGENTS.md has **no import mechanism** — must be complete and self-contained
- Natively read by 5+ tools (Codex, Copilot, Cursor, Windsurf, OpenCode)
- CLAUDE.md is only natively read by Claude Code
- Add rules only after observed failures — each speculative rule adds ~20% token overhead with no upside

### Structure
- Keep under **150-200 lines** — critical rules at the top (agents lose fidelity in the middle)
- Place at repo root; subdirectory AGENTS.md files override parent for that path (monorepos)
- Do NOT auto-generate wholesale with an LLM — curate manually

### Required Sections

```markdown
# AGENTS.md — [Project Name]

## Project Overview
## Tech Stack
## Key Commands
## Non-Obvious Patterns
## Code Style
## Testing Rules
## Boundaries
  ### Always (no approval needed)
  ### Ask First
  ### Never
## Known Issues
```

### Rules
- **Key Commands**: exact shell commands for install, dev, build, test, lint, single-test, watch
- **Non-Obvious Patterns**: counterintuitive decisions with one-line mechanism explanation each
- **Boundaries**: three tiers — always-safe / ask-first / never. Be explicit
- **Code Style**: one representative code snippet beats three paragraphs of prose
- Exclude: content already in README, standard language conventions, frequently-changing info
- Treat as code: PR-review updates, remove stale rules aggressively

## CLAUDE.md Rules

### Role: Claude adapter over AGENTS.md
CLAUDE.md is the Claude Code adapter. It:
1. Imports AGENTS.md via `@AGENTS.md` as the **first line** — no exceptions
2. Adds only Claude Code-specific content below that import
3. Never duplicates content that lives in AGENTS.md

If there are zero Claude-specific additions, use a symlink (non-Windows only):
```bash
ln -s AGENTS.md CLAUDE.md
```
Prefer `@` import for portability and future Claude-specific extensions.

### Load order (broadest to narrowest)
1. `/Library/Application Support/ClaudeCode/CLAUDE.md` (managed policy, macOS)
2. `~/.claude/CLAUDE.md` (user prefs)
3. `~/.claude/rules/*.md` (modular user prefs)
4. `./CLAUDE.md` (project, committed to git) ← this is what we generate
5. `./.claude/rules/*.md` (path-scoped project rules)
6. `./CLAUDE.local.md` (personal overrides, gitignored)

### Required Structure

```markdown
@AGENTS.md

# [Project Name] — Claude Code

## Commands        (only if different from AGENTS.md)
## Important Constraints
## References
```

### Rules
- **First line must be** `@AGENTS.md`
- Target under **200 lines** total — use `.claude/rules/` for overflow
- Use `IMPORTANT:` prefix for constraints Claude most commonly forgets
- Be concrete: "Run `npm test` before committing" > "test your changes"
- Path-scoped rules in `.claude/rules/` load only when matching files are open
- Do NOT include: file-by-file tours, tutorials, standard conventions already in AGENTS.md
- Do NOT symlink CLAUDE.md → AGENTS.md (wrong direction)

### Path-scoped rule file (`.claude/rules/api.md`)
```markdown
---
paths:
  - "src/api/**/*.ts"
---
- All endpoints must include Zod input validation
- Use the standard error format from `src/lib/errors.ts`
```

## Templates

See `templates/` for ready-to-fill templates:
- [AGENTS template](templates/AGENTS.md)
- [CLAUDE template](templates/CLAUDE.md)
- [README template](templates/README.md)
- [CONTRIBUTING template](templates/CONTRIBUTING.md)

## Checklist Before Done

- [ ] AGENTS.md is the canonical source, under 200 lines, critical rules at top
- [ ] CLAUDE.md first line is `@AGENTS.md`
- [ ] No content duplicated between AGENTS.md and CLAUDE.md
- [ ] README.md has working copy-paste Quick Start and Mermaid diagram
- [ ] CONTRIBUTING.md has explicit DCO/CLA section and security disclosure path
- [ ] All commands verified against actual package.json / Makefile / pyproject.toml scripts

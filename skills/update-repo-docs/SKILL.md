---
name: update-repo-docs
description: Audit and update AGENTS.md, README.md, CONTRIBUTING.md, and CLAUDE.md in the current repo. Detects staleness, removes AI slop, validates factual correctness with HITL confirmation before writing.
disable-model-invocation: true
argument-hint: [--file <AGENTS|README|CONTRIBUTING|CLAUDE|all>]
tool: shared
---

# Update Repo Docs

Audit and update the four canonical documentation files in the current repository. Uses a **Human-in-the-Loop (HITL)** gate before any write to ensure correctness.

## When to Use

- After significant code changes that make existing docs stale
- When docs contain AI slop (vague prose, hedging language, filler sections)
- Before a release or significant PR to ensure docs reflect reality
- When the user says "update the docs", "fix the README", "clean up AGENTS.md"

## Phase 1 — Audit (Read Only)

**Never write anything in this phase.**

Run all of the following before drafting any changes:

```bash
# What's actually in the repo
git log --oneline -10
git diff HEAD~5..HEAD --stat

# Verify commands still exist
cat pyproject.toml         # scripts, entry points
cat Makefile 2>/dev/null   # or Taskfile.yml, package.json
ls src/ tests/

# Verify agent/skill counts
ls agents/ | wc -l
ls skills/ | wc -l

# Check for stale references in docs
grep -n "maestro" AGENTS.md README.md 2>/dev/null
grep -n "[0-9]\+ agents" README.md AGENTS.md 2>/dev/null
grep -n "[0-9]\+ skills" README.md AGENTS.md 2>/dev/null
```

Then read the current state of each doc file being updated.

## Phase 2 — Diff Draft

Produce a **numbered change list** — do not write files yet. Format:

```
### AGENTS.md
1. Line 6: "191 agents" → "84 agents"  (verified: `ls agents/ | wc -l` = 84)
2. Line 45: remove `maestro.md` reference  (file does not exist: `ls agents/maestro.md`)
3. Lines 12–18: Vague intro paragraph → replace with [concrete one-liner]

### README.md
4. Line 5: "191 subagents" → "84 agents"
5. Lines 40–46: `maestro.md` in tree → remove
```

## Phase 3 — HITL Gate (Mandatory)

**Stop. Show the diff draft to the user. Ask for confirmation.**

Use the `AskUserQuestion` tool with two questions:

1. **"Which changes should I apply?"** — list each numbered change as an option; allow multi-select. Include "All of the above" and "None — abort" options.
2. **"Are there corrections or additions I missed?"** — free-text, allow the user to redirect.

Only proceed to Phase 4 after the user confirms. If the user picks "None — abort", stop.

## Phase 4 — Apply Approved Changes

Apply only the changes the user approved. For each change:
1. Show the before/after diff inline (one block per file)
2. Write the file
3. Mark the change as done in the numbered list

After all writes:

```bash
# Verify CLAUDE.md still starts with @AGENTS.md
head -1 CLAUDE.md

# Verify no broken cross-references remain
grep -n "@AGENTS.md" CLAUDE.md
```

## AI Slop Detection Rules

Flag any of the following as slop — they add tokens with zero information:

| Pattern | Example | Fix |
|---------|---------|-----|
| Filler opener | "This document provides..." | Delete the sentence |
| Hedge clusters | "may", "might", "could be", "in some cases" | Make declarative or delete |
| Meta-commentary | "Note that...", "It's worth mentioning..." | Delete the wrapper, keep the fact |
| Stale counts | "191 agents" when `ls agents/ \| wc -l` = 84 | Update to verified count |
| Non-existent files | `maestro.md`, `sync-primary-agents.sh` | Remove or replace |
| Aspirational sections | "Coming soon", "Future work" without dates | Remove entirely |
| Redundant restatement | README duplicating AGENTS.md word-for-word | Cut to a one-liner + link |
| Emoji overload | 5+ emojis per section in a technical doc | Keep ≤1 per major section or none |
| Passive voice chains | "agents are managed by the system which is configured by..." | Rewrite active |

## Correctness Validation Checklist

Before proposing any change, verify it against the actual repo state:

- [ ] Command names match `pyproject.toml` `[project.scripts]` or Makefile targets
- [ ] File paths exist: `ls <path>` before referencing them
- [ ] Agent count matches `ls agents/ | wc -l`
- [ ] Skill count matches `ls skills/ | wc -l`
- [ ] `CLAUDE.md` first line is `@AGENTS.md`
- [ ] No references to deleted files (grep for filename, confirm `ls` returns nothing)
- [ ] Tier names match actual files in `tiers/` (if applicable)
- [ ] Model names in docs match currently configured models (check `opencode.jsonc` or `oh-my-openagent.jsonc`)

## AGENTS.md-Specific Rules

- Keep under 200 lines — flag if over
- Critical rules must appear in the top half of the file
- Three tiers in Boundaries section: Always / Ask First / Never
- Remove rules that haven't been violated in the last 3 months (ask the user)

## README.md-Specific Rules

- Quick Start must be copy-paste executable top to bottom
- Verify every command in Quick Start actually works
- Badge row: max 8 badges, single row
- No "Coming soon" sections without a date
- Mermaid diagram should reflect current architecture (regenerate if stale)

## CONTRIBUTING.md-Specific Rules

- DCO or CLA section must be present and accurate
- Dev setup commands must match current `pyproject.toml` / `package.json`
- Security disclosure path must have a real contact (email or private advisory link)

## CLAUDE.md-Specific Rules

- First line must be `@AGENTS.md` — no exceptions
- Everything below must be Claude Code-specific (not duplicating AGENTS.md)
- Flag any content that belongs in AGENTS.md instead

## Anti-Patterns

- **Never write first, ask later** — HITL gate is mandatory
- **Never guess counts** — always run `ls | wc -l` or grep to verify
- **Never propose a change you haven't verified against the file system**
- **Never remove content without telling the user why** — show the slop pattern that triggered it
- **Never update README and AGENTS.md to say different things** — one source of truth

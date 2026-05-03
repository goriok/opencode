# AGENTS.md — opencode Global Configuration Repository

This file provides guidance for AI coding agents operating in this repository.

---

## Repository Overview

This is the **global opencode configuration directory** (`~/.config/opencode`), not an application codebase.
Its purpose is to define and distribute AI sub-agent personas for the [opencode](https://opencode.ai) CLI,
and to mirror those agents to `.cursor/rules/` for Cursor IDE compatibility.

**Tracked files** (only these are in git):
- `opencode.json` — global opencode config
- `setup.sh` — one-time machine setup script
- `install-agents.sh` — per-project agent installer
- `AGENTS.md` — this file
- `agents/alan-turing.md` — primary agent: SDLC orchestrator (tracked exception)
- `agents/grace-hopper.md` — primary agent: troubleshooting orchestrator (tracked exception)
- `agents/ada-lovelace.md` — primary agent: analysis orchestrator (tracked exception)
- `agents/maestro.md` — primary agent: legacy orchestrator (tracked exception, superseded by Alan Turing)
- `skills/` — team-shareable skill definitions (all tracked)

**Gitignored** (generated at runtime, do not commit):
- `agents/` — 191 installed opencode agent `.md` files from agency-agents (exception: primary agents above)
- `.opencode/` — runtime opencode directory
- `.cursor/` — Cursor IDE rule files (`.mdc`)
- `node_modules/`, `package.json`, `bun.lock`

---

## Commands

### Setup (run once per machine)

```bash
bash ~/.config/opencode/setup.sh
```

Clones [agency-agents](https://github.com/msitarzewski/agency-agents), converts, and installs agent
definitions to `~/.config/opencode/agents/`. Also runs `sync-primary-agents.sh` automatically.

### Sync primary agents to Claude Code

```bash
bash ~/.config/opencode/sync-primary-agents.sh
```

Copies `alan-turing.md`, `grace-hopper.md`, and `maestro.md` from `~/.config/opencode/agents/` to
`~/.claude/agents/`, stripping opencode-specific fields (`mode`, `permission`) that Claude Code does
not support. Run this after editing any primary agent file.

**Source of truth:** `~/.config/opencode/agents/*.md`
**Claude Code mirror:** `~/.claude/agents/*.md` (generated — do not edit directly)

### Per-project Agent Installation

```bash
# From inside a project root:
bash ~/.config/opencode/install-agents.sh

# With explicit target:
bash ~/.config/opencode/install-agents.sh /path/to/project
```

Installs agents to `<target>/.opencode/agents/`.

### Tests

**There are no tests.** This is a configuration/agent-definition repository with no application logic
to test. Do not add a test runner without explicit instruction.

### Lint / Format

**There is no linter or formatter configured.** Shell scripts follow consistent style conventions
(see below). Do not add linting tooling without explicit instruction.

### Package Manager

**Bun** is the package manager (`bun.lock` present). If you need to install dependencies:

```bash
bun install
```

---

## Shell Script Style Guide

All Bash scripts in this repo (`setup.sh`, `install-agents.sh`) follow these conventions:

### Header

Every script starts with:
```bash
#!/usr/bin/env bash
#
# script-name.sh — one-line description
#
# Usage:
#   bash <invocation>
#
# What it does:
#   1. Step one
#   2. Step two
```

### Safety flags

Always use at the top of every script, immediately after the header comment:
```bash
set -euo pipefail
```

### Logging helpers

Define and use colored logging helpers — never use raw `echo` for user-facing output:
```bash
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { printf "${GREEN}[opencode]${NC} %s\n" "$*"; }
warn()  { printf "${YELLOW}[opencode]${NC} %s\n" "$*"; }
error() { printf "${RED}[opencode]${NC} %s\n" "$*" >&2; exit 1; }
```

- `info` — normal progress messages (green)
- `warn` — non-fatal warnings (yellow), script continues
- `error` — fatal errors (red), prints to stderr and exits

### Temp directories

Always use `mktemp -d` and clean up with a `trap`:
```bash
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
```

### Variables

- Use `UPPER_SNAKE_CASE` for all variables
- Quote all variable expansions: `"$VAR"`, `"${VAR:-default}"`
- Use `${1:-$PWD}` pattern for optional positional arguments with defaults

### Conditionals

Use `[[ ... ]]` (not `[ ... ]`) for all conditionals:
```bash
if [[ -d "$AGENTS_DIR" ]]; then
  warn "Already installed at $AGENTS_DIR"
  exit 0
fi
```

### Subshells for directory changes

Use a subshell instead of `cd && command` to avoid side effects:
```bash
(cd "$TARGET_DIR" && bash some-script.sh)
```

### Counting files

```bash
COUNT=$(ls "$DIR"/*.md 2>/dev/null | wc -l | tr -d ' ')
```

---

## Agent Definition File Style Guide

Agent definitions are Markdown files with YAML frontmatter. They live in `agents/*.md` (gitignored,
installed by `setup.sh`).

### Frontmatter (opencode format)

```yaml
---
name: Human Readable Name
description: One-line description of this agent's role and specialty.
mode: subagent
color: '#hexcolor'
---
```

### Frontmatter (Cursor MDC format)

```yaml
---
description: One-line description.
globs: ""
alwaysApply: false
---
```

### File naming

- `kebab-case.md` / `kebab-case.mdc`
- Name should match the agent's specialty, e.g. `senior-developer.md`, `code-reviewer.md`

### Body structure

Agents follow a consistent section order using emoji headers:

```markdown
## 🧠 Your Identity & Memory
## 🎯 Your Core Mission
## 🚨 Critical Rules
## 🔄 Learning & Memory
## 🚀 Advanced Capabilities
```

- Open with a bold persona declaration: `**AgentName**`
- Use `🔴` for blockers, `🟡` for suggestions, `💭` for nits (especially in review agents)
- Include fenced code blocks with explicit language tags for all examples
- Use tables for comparison matrices and decision grids
- Close with an `**Instructions Reference**` line pointing to the canonical source

---

## opencode Configuration (`opencode.jsonc`)

```json
{
  "$schema": "https://opencode.ai/config.json",
  "autoupdate": true,
  "permission": {
    "edit": "ask",
    "bash": "ask"
  },
  "mcp": {
    "memory": {
      "type": "local",
      "command": ["npx", "-y", "@modelcontextprotocol/server-memory"],
      "enabled": false
    }
  },
  "plugin": [
    "@tarquinen/opencode-dcp@latest",
    "opencode-mem",
    "oh-my-openagent",
    "opencode-workspace"
  ]
}
```

- `permission.edit` and `permission.bash` are both `"ask"` — agents must prompt before editing files
  or running shell commands
- **Note**: The `memory` MCP is **disabled** to avoid conflict with `opencode-mem` plugin
- The `opencode-mem` plugin manages persistent memory via its own MCP server

### Configuration Files

| File | Purpose |
|------|---------|
| `opencode.jsonc` | Main configuration |
| `dcp.jsonc` | Dynamic Context Pruning |
| `opencode-mem.jsonc` | Persistent memory (web UI: port 4747) |
| `oh-my-openagent.jsonc` | Model configs, hooks, agent assignments |

---

## Primary Agents (Orchestrators)

These are tracked custom agents that orchestrate specialist squads under the AI Fluency Framework 4Ds,
ISO-25010, ATAM, and RM-ODP. They reference subagents from the agency-agents collection by name.

| Agent | File | Purpose |
|---|---|---|
| **Alan Turing** | `agents/alan-turing.md` | SDLC orchestrator — requirements through monitoring |
| **Grace Hopper** | `agents/grace-hopper.md` | Troubleshooting orchestrator — detection through prevention |
| **Margaret Hamilton** | `agents/margaret-hamilton.md` | Deep analysis orchestrator — full ATAM, ISO-25010 |
| **Ada Lovelace** | `agents/ada-lovelace.md` | Exploratory analysis — fast, lightweight |
| **Maestro** | `agents/maestro.md` | Legacy orchestrator — superseded by Alan Turing *(file missing from disk)* |

### Integrated Frameworks

All primary agents apply:
- **AI Fluency 4Ds**: Delegation, Description, Discernment, Diligence
- **ISO-25010**: Quality attribute evaluation at Requirements and Testing phases
- **ATAM**: Architectural tradeoff analysis at Architecture phase; retrospective at RCA
- **RM-ODP**: Five-viewpoint summary at Documentation phase; fault localization in post-mortem

### Companion Skills

Each primary agent has a companion skill for direct invocation:

| Skill | File | Invocation |
|---|---|---|
| `alan-turing` | `skills/alan-turing/SKILL.md` | `/alan-turing` (opencode) / Skill tool (Claude Code) |
| `grace-hopper` | `skills/grace-hopper/SKILL.md` | `/grace-hopper` (opencode) / Skill tool (Claude Code) |
| `margaret-hamilton` | `skills/margaret-hamilton/SKILL.md` | `/margaret-hamilton` (opencode) / Skill tool |
| `ada-lovelace` | `skills/ada-lovelace/SKILL.md` | `/ada-lovelace` (opencode) / Skill tool (Claude Code) |

### Subagent References

Primary agents reference agency-agents subagents by their installed slug names. Run `setup.sh` to
install them. Key subagents used:

**Alan Turing squad:** `product-manager`, `software-architect`, `backend-architect`,
`security-engineer`, `senior-developer`, `frontend-developer`, `database-optimizer`,
`code-reviewer`, `api-tester`, `performance-benchmarker`, `evidence-collector`,
`reality-checker`, `accessibility-auditor`, `devops-automator`, `sre`,
`git-workflow-master`, `incident-response-commander`, `technical-writer`, `compliance-auditor`

**Grace Hopper squad:** `incident-response-commander`, `sre`, `infrastructure-maintainer`,
`backend-architect`, `security-engineer`, `database-optimizer`, `devops-automator`,
`code-reviewer`, `software-architect`, `senior-developer`, `api-tester`,
`performance-benchmarker`, `compliance-auditor`, `test-results-analyzer`, `technical-writer`

**Ada Lovelace squad:** `software-architect`, `backend-architect`, `security-engineer`,
`code-reviewer`, `senior-developer`, `database-optimizer`, `data-engineer`,
`performance-benchmarker`, `api-tester`, `evidence-collector`, `reality-checker`,
`infrastructure-maintainer`, `sre`, `devops-automator`, `accessibility-auditor`,
`compliance-auditor`, `analytics-reporter`, `technical-writer`, `product-manager`

---

## Installed Plugins & Coexistence

This workspace uses a multi-plugin setup with harmonic agent coexistence:

### Plugins

| Plugin | Purpose | Config File |
|--------|---------|------------|
| `opencode-mem` | Persistent memory, vector DB | `opencode-mem.jsonc` |
| `oh-my-openagent` | Full Arsenal, hooks, ultrawork | `oh-my-openagent.jsonc` |
| `opencode-workspace` | Multi-agent bundle | `opencode-workspace.jsonc` |
| `@tarquinen/opencode-dcp` | Context pruning | `dcp.jsonc` |

### Agent Layers

The system uses delegating layers:

| Layer | Agent | Purpose |
|------|-------|---------|
| **Strategy** | Alan Turing, Grace Hopper, Ada Lovelace | High-level decisions |
| **Specialist** | workspace (researcher, reviewer) | Research & review |
| **Quick** | oh-my-openagent (Sisyphus, Oracle) | Fast execution |

### Decision Tree

```
→ Feature complete  → Alan Turing
→ Bug/incident  → Grace Hopper
→ Analysis     → Ada Lovelace
→ Quick fix    → oh-my-openagent
→ Remember    → opencode-mem
→ Large context → dcp compress
```

---

## Important Notes for Agents

- **Do not commit** `agents/` (except tracked primary agents above), `.opencode/`, `.cursor/`, `node_modules/`, `package.json`, or `bun.lock`
- **Do not create** application source files, test files, or build configs unless explicitly asked
- **Do not modify** `opencode.json` permission gates without explicit user approval
- The `.cursor/rules/*.mdc` files are auto-generated mirrors of `agents/*.md`; edit the source `.md`
  files, not the `.mdc` files directly
- When adding a new agent, follow the YAML frontmatter and body structure above exactly
- Primary agents (`mode: primary`) are tracked in git; subagents (`mode: subagent`) are gitignored

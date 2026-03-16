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

**Gitignored** (generated at runtime, do not commit):
- `agents/` — 156 installed opencode agent `.md` files
- `.opencode/` — runtime opencode directory
- `.cursor/` — Cursor IDE rule files (`.mdc`)
- `node_modules/`, `package.json`, `bun.lock`

---

## Commands

### Setup (run once per machine)

```bash
bash ~/.config/opencode/setup.sh
```

Clones [agency-agents](https://github.com/msitarzewski/agency-agents), converts, and installs 156 agent
definitions to `~/.config/opencode/agents/`.

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

## opencode Configuration (`opencode.json`)

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
      "enabled": true
    }
  }
}
```

- `permission.edit` and `permission.bash` are both `"ask"` — agents must prompt before editing files
  or running shell commands
- The `memory` MCP server is always enabled; use it to persist context across sessions

---

## Important Notes for Agents

- **Do not commit** `agents/`, `.opencode/`, `.cursor/`, `node_modules/`, `package.json`, or `bun.lock`
- **Do not create** application source files, test files, or build configs unless explicitly asked
- **Do not modify** `opencode.json` permission gates without explicit user approval
- The `.cursor/rules/*.mdc` files are auto-generated mirrors of `agents/*.md`; edit the source `.md`
  files, not the `.mdc` files directly
- When adding a new agent, follow the YAML frontmatter and body structure above exactly

# AGENTS.md — opencode Global Configuration Repository

This file provides guidance for AI coding agents operating in this repository.

---

## Repository Overview

This is the **global opencode configuration directory** (`~/.config/opencode`), not an application codebase.
Its purpose is to define and distribute AI sub-agent personas for the [opencode](https://opencode.ai) CLI,
and to mirror those agents to `~/.claude/agents/` for Claude Code compatibility.

**Tracked files** (only these are in git):
- `opencode.jsonc` — global opencode config (note: `.jsonc`, not `.json`)
- `setup.sh` — one-time machine setup script
- `install-agents.sh` — per-project agent installer
- `sync-primary-agents.sh` — mirrors primary agents to Claude Code
- `AGENTS.md` — this file
- `agents/` — all 165 agent `.md` files are tracked (all committed, not gitignored)
- `skills/` — team-shareable skill definitions (all tracked)

**Gitignored** (do not commit):
- `.opencode/` — runtime opencode directory
- `.cursor/` — Cursor IDE rule files
- `node_modules/`, `package.json`, `bun.lock`

> **Common mistake:** `AGENTS.md` and the README previously described `agents/` as gitignored. It is NOT.
> All 165 agent files are tracked in git. The `.gitignore` only excludes `.opencode/`, `.cursor/`, and `node_modules/`.

---

## Commands

### Setup (run once per machine)

```bash
bash ~/.config/opencode/setup.sh
```

Clones [agency-agents](https://github.com/msitarzewski/agency-agents), converts agents to opencode
format, copies them to `~/.config/opencode/agents/`, then calls `sync-primary-agents.sh` automatically.

Note: `setup.sh` runs `convert.sh` **without** the `--tool opencode` flag (the flag is only used in `install-agents.sh`).

### Sync primary agents to Claude Code

```bash
bash ~/.config/opencode/sync-primary-agents.sh
```

Strips `mode` and `permission` frontmatter fields (not supported by Claude Code) and copies these files
to `~/.claude/agents/`:
- `alan-turing.md`, `grace-hopper.md`, `tony-hoare.md`, `ada-lovelace.md`, `agents-orchestrator.md`

**Source of truth:** `~/.config/opencode/agents/*.md`
**Claude Code mirror:** `~/.claude/agents/*.md` — do not edit directly

Run after editing any primary agent file.

### Per-project Agent Installation

```bash
# From inside a project root:
bash ~/.config/opencode/install-agents.sh

# With explicit target:
bash ~/.config/opencode/install-agents.sh /path/to/project
```

Installs agents to `<target>/.opencode/agents/`. Exits with a warning if the directory already exists.

### Package Manager

**npm** is the package manager (`package-lock.json` present). The `opencode.jsonc` references
`@opencode-ai/plugin` via `package.json` (managed by opencode itself — do not modify manually):

```bash
npm install
```

### Tests / Lint

**None configured.** Do not add a test runner or linter without explicit instruction.

---

## opencode Configuration (`opencode.jsonc`)

- `permission.edit` and `permission.bash` are both `"ask"` — agents must prompt before editing or running commands
- `model: github-copilot/claude-opus-4-6` — provedor padrão neste ambiente é GitHub Copilot
- MCP `memory` persists context across sessions via `@modelcontextprotocol/server-memory` (disabled aqui — `opencode-mem` plugin substitui)
- MCP `idpa-api` integra com a API IDPA local
- MCP `kanban-force` integra com o Kanban Force corporativo
- MCP `gitlab` connects to `https://gitlab.luizalabs.com` using `$GITLAB_PERSONAL_ACCESS_TOKEN` env var; TLS verification is disabled (`NODE_TLS_REJECT_UNAUTHORIZED=0`)
- MCP `mcp-atlassian` integra com Confluence corporativo

### Plugin Ecosystem

Cinco plugins trabalham em camadas:

| Plugin                       | Purpose              | Config                  | Key Feature                              |
| ---------------------------- | -------------------- | ----------------------- | ---------------------------------------- |
| **opencode-mem**             | Memória persistente  | `opencode-mem.jsonc`    | Vector DB, Web UI (port 4747)            |
| **oh-my-openagent**          | Arsenal + hooks      | `oh-my-openagent.jsonc` | Hooks (thinking-block, context-monitor)  |
| **opencode-workspace**       | Multi-agent bundle   | *(plugin config)*       | Researcher, coder, scribe, reviewer      |
| **@tarquinen/opencode-dcp**  | Context pruning      | `dcp.jsonc` (gerado)    | Auto-compress quando o contexto enche    |

> **Nota sobre `oh-my-openagent.jsonc`**: os blocos `agents` e `categories` mapeiam agents para modelos z.ai via LiteLLM proxy. Para que o roteamento funcione, o proxy deve estar rodando: `task litellm:up`.

---

## Primary Agents (Orchestrators)

These five agents are the only custom ones defined here. All other agents come from [agency-agents](https://github.com/msitarzewski/agency-agents).

| Agent | File | Purpose |
|---|---|---|
| **Alan Turing** | `agents/alan-turing.md` | SDLC orchestrator — requirements through monitoring |
| **Grace Hopper** | `agents/grace-hopper.md` | Troubleshooting orchestrator — detection through prevention |
| **Tony Hoare** | `agents/tony-hoare.md` | Fix orchestrator — contract verification through regression defense (activates after RCA ≥ 7/10) |
| **Ada Lovelace** | `agents/ada-lovelace.md` | Analysis orchestrator — scope through validation, ATAM-driven |
| **Agents Orchestrator** | `agents/agents-orchestrator.md` | General orchestrator (legacy `maestro.md` does not exist) |

### Agent Invocation

**In opencode:** Primary agents are invoked directly as `@alan-turing`, `@grace-hopper`, `@tony-hoare`, `@ada-lovelace`, `@margaret-hamilton`

**In Claude Code:** Primary agents have companion skills available via the Skill tool (maintained in `~/.claude/skills/`)

### Specialized Skills (opencode only)

| Skill | File | Purpose |
|---|---|---|
| `agents-feature-builder` | `skills/agents-feature-builder/SKILL.md` | Orchestrates feature implementation squad |
| `agents-troubleshooter` | `skills/agents-troubleshooter/SKILL.md` | Orchestrates troubleshooting squad |
| `bug-fix` | `skills/bug-fix/SKILL.md` | Guidelines for bug diagnosis and fixing |
| `code-review` | `skills/code-review/SKILL.md` | Guidelines for code review process |
| `conventional-commits` | `skills/conventional-commits/SKILL.md` | Commit message formatting rules |
| `gitlab-mr-create` | `skills/gitlab-mr-create/SKILL.md` | GitLab MR creation with auto-generated description |
| `gitlab-mr-review` | `skills/gitlab-mr-review/SKILL.md` | GitLab MR review orchestration |
| `rfc-template` | `skills/rfc-template/SKILL.md` | RFC template for technical decisions |
| `tdd` | `skills/tdd/SKILL.md` | Test-driven development guidelines |
| `kanban-force-card` | `skills/kanban-force-card/SKILL.md` | Cria, atualiza, move e comenta cards no Kanban Force via MCP |
| `kanban-force-planner` | `skills/kanban-force-planner/SKILL.md` | Planejamento e organização de demandas no Kanban Force |
| `gitlab-mr-fixes` | `skills/gitlab-mr-fixes/SKILL.md` | Aplicação de fixes em MRs do GitLab |
| `change-request-create` | `skills/change-request-create/SKILL.md` | Criação de change request |
| `changelog-update` | `skills/changelog-update/SKILL.md` | Atualização de changelog |
| `cve-impact-analysis` | `skills/cve-impact-analysis/SKILL.md` | Análise de impacto de CVE |

### Companion Skills (orchestrators primários)

Skills que carregam o framework completo de cada primary agent:

| Skill | Companion para | Invocação |
|---|---|---|
| `alan-turing` | `agents/alan-turing.md` | `/alan-turing` (opencode) |
| `grace-hopper` | `agents/grace-hopper.md` | `/grace-hopper` (opencode) |
| `ada-lovelace` | `agents/ada-lovelace.md` | `/ada-lovelace` (opencode) |
| `margaret-hamilton` | `agents/margaret-hamilton.md` | `/margaret-hamilton` (opencode) |

---

## Shell Script Style Guide

All Bash scripts (`setup.sh`, `install-agents.sh`, `sync-primary-agents.sh`) follow these conventions:

- **Safety flags** immediately after header: `set -euo pipefail`
- **Logging helpers** — never raw `echo`:
  ```bash
  info()  { printf "${GREEN}[opencode]${NC} %s\n" "$*"; }
  warn()  { printf "${YELLOW}[opencode]${NC} %s\n" "$*"; }
  error() { printf "${RED}[opencode]${NC} %s\n" "$*" >&2; exit 1; }
  ```
- **Temp dirs** with trap cleanup: `TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT`
- **Variables**: `UPPER_SNAKE_CASE`, always quoted (`"$VAR"`, `"${VAR:-default}"`)
- **Conditionals**: `[[ ... ]]` not `[ ... ]`
- **Directory changes**: subshell `(cd "$DIR" && cmd)` not `cd && cmd`

---

## Agent Definition File Style Guide

Agent definitions are Markdown files with YAML frontmatter in `agents/*.md`.

### Frontmatter (opencode format)

```yaml
---
name: Human Readable Name
description: One-line description of this agent's role and specialty.
mode: subagent
color: '#hexcolor'
---
```

`mode: primary` is used only for the four orchestrators above. Claude Code does not support `mode` or `permission` — `sync-primary-agents.sh` strips them automatically.

### File naming

`kebab-case.md` matching the agent's specialty (e.g. `senior-developer.md`).

### Body structure

```markdown
## 🧠 Your Identity & Memory
## 🎯 Your Core Mission
## 🚨 Critical Rules
## 🔄 Learning & Memory
## 🚀 Advanced Capabilities
```

- Open with a bold persona declaration: `**AgentName**`
- Use `🔴` blockers, `🟡` suggestions, `💭` nits (review agents)
- Fenced code blocks with explicit language tags on all examples
- Close with `**Instructions Reference**` pointing to canonical source

---

## Important Notes for Agents

- **Do not commit** `.opencode/`, `.cursor/`, `node_modules/`, `package.json`, `bun.lock`
- **`agents/` IS tracked** — all 165 files are in git; do not treat them as gitignored
- **Do not edit** `~/.claude/agents/*.md` directly — they are mirrors generated by `sync-primary-agents.sh`
- **Do not modify** `opencode.jsonc` permission gates without explicit user approval
- **`maestro.md` does not exist** — the legacy orchestrator reference in older docs is stale; use `agents-orchestrator.md`
- The config file is `opencode.jsonc` (with `.jsonc` extension), not `opencode.json`

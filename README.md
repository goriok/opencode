# ⚡ OpenCode Configuration

> Global configuration, agent personas, plugins, and operational tooling for the [opencode](https://opencode.ai) CLI.

This repository manages the shared AI agent ecosystem for OpenCode — **191 subagents**, **5 primary orchestrators**, **12 skills**, **4 plugins** — all coordinated through layered orchestration with ISO-25010, ATAM, and RM-ODP frameworks.

---

## 🚀 Quick Start

```bash
# Clone
git clone <repo-url> ~/.config/opencode
cd ~/.config/opencode

# Install the CLI
uv tool install --editable .

# Install everything (agents + sync to Claude Code)
ocx setup

# Start the LiteLLM proxy
ocx litellm setup
```

After setup, OpenCode will have all 191 agents installed and the primary orchestrators synced to Claude Code.

---

## 📁 Repository Structure

```
~/.config/opencode/
├── AGENTS.md                    # Agent guidance (for AI agents operating in this repo)
├── README.md                    # This file
├── opencode.jsonc               # Main OpenCode configuration
├── pyproject.toml               # Python package for the `ocx` CLI
├── src/ocx/                      # CLI source (commands: setup, agents, litellm, shortcuts, …)
│
├── agents/                      # 191 agent .md files (all tracked in git, installed by ocx setup)
│   ├── alan-turing.md           #   ↳ Tracked: SDLC orchestrator
│   ├── grace-hopper.md          #   ↳ Tracked: Troubleshooting orchestrator
│   ├── ada-lovelace.md          #   ↳ Tracked: Exploratory analysis
│   ├── margaret-hamilton.md     #   ↳ Tracked: Deep analysis
│   └── maestro.md              #   ↳ Tracked: Legacy (superseded)
│
├── skills/                      # Companion skills for primary agents
│   ├── alan-turing/             #   /alan-turing invocation
│   ├── grace-hopper/            #   /grace-hopper invocation
│   ├── ada-lovelace/            #   /ada-lovelace invocation
│   ├── margaret-hamilton/       #   /margaret-hamilton invocation
│   ├── bug-fix/                 #   Bug diagnosis & fix
│   ├── code-review/             #   Code review guidelines
│   ├── conventional-commits/    #   Commit message rules
│   ├── gitlab-mr-review/        #   GitLab MR review orchestration
│   ├── rfc-template/            #   RFC template (RM-ODP + ISO-25010)
│   ├── tdd/                     #   Test Driven Development
│   ├── agents-feature-builder/  #   Feature squad orchestrator
│   └── agents-troubleshooter/   #   Troubleshooting squad orchestrator
│
├── docs/
│   ├── handbook/                # Reference documentation (how things work)
│   │   ├── README.md            #   Plugins overview & decision tree
│   │   ├── dcp.md               #   Dynamic Context Pruning
│   │   ├── oh-my-openagent.md   #   Arsenal + hooks + ultrawork
│   │   ├── opencode-mem.md      #   Persistent memory with vector DB
│   │   ├── opencode-workspace.md #   Multi-agent bundle
│   │   └── agent-vocabulary.md  #   Vocabulary & frameworks for agents
│   ├── handbooks/               # Detailed guides
│   │   ├── opencode-go-guia-modelos.md  # OpenCode Go model guide
│   │   └── token-tracker.md     # Token dashboard reference
│   ├── madr/                    # Architecture Decision Records
│   │   ├── README.md            #   MADR index
│   │   ├── 0001-*.md            #   Token tracking via Bash + SQLite
│   │   ├── 0002-*.md            #   Primary agent orchestration
│   │   ├── 0003-*.md            #   Plugin coexistence strategy
│   │   └── 0004-*.md            #   Self-contained HTML dashboard
│   └── runbooks/                # Step-by-step operational procedures
│       ├── README.md            #   Runbook index
│       ├── rb-001-*.md          #   New machine setup
│       ├── rb-002-*.md          #   Token dashboard generation
│       ├── rb-003-*.md          #   Troubleshoot empty dashboard
│       ├── rb-004-*.md          #   Adding a primary agent
│       ├── rb-005-*.md          #   Updating agency-agents
│       └── rb-006-*.md          #   Baseline strategy comparison
│
├── thoughts/                    # Design docs & plans
│   └── shared/
│       ├── designs/             #   Validated design documents
│       └── plans/               #   Implementation plans
│
├── token-baselines/             # Baseline snapshots (gitignored)
└── token-dashboard.html         # Generated dashboard (gitignored)
```

---

## 🤖 Primary Agents

Five orchestrators coordinate specialist subagents under structured frameworks:

| Agent | Invocation | Purpose | Framework |
|-------|-----------|---------|-----------|
| **Alan Turing** | `/alan-turing` | SDLC: requirements → monitoring | ISO-25010, ATAM, RM-ODP |
| **Grace Hopper** | `/grace-hopper` | Troubleshooting: detection → prevention | ISO-25010, ATAM RCA |
| **Margaret Hamilton** | `/margaret-hamilton` | Deep analysis: ATAM, profiling | ISO-25010, RM-ODP |
| **Ada Lovelace** | `/ada-lovelace` | Fast exploration, pattern discovery | Lightweight, no heavy docs |
| **Maestro** | *(legacy)* | Superseded by Alan Turing | — |

### Decision Tree

```
→ New feature?          → /alan-turing
→ Bug / incident?       → /grace-hopper
→ Deep analysis / RFC?  → /margaret-hamilton
→ Quick investigation?  → /ada-lovelace
→ Code review?          → /code-review skill
→ Just remember X?      → opencode-mem
→ Running out of ctx?   → /dcp compress
```

### Subagent Squads

Each primary agent delegates to a squad of 15-19 specialist subagents from the agency-agents collection (installed by `ocx setup`). See [AGENTS.md](./AGENTS.md) for the full squad rosters.

---

## 🔌 Plugin Ecosystem

Four plugins work in harmonic layers:

| Plugin | Purpose | Config | Key Feature |
|--------|---------|--------|-------------|
| **opencode-mem** | Persistent memory | `opencode-mem.jsonc` | Vector DB, Web UI (port 4747) |
| **oh-my-openagent** | Arsenal + hooks | `oh-my-openagent.jsonc` | Sisyphus, Oracle, ultrawork mode |
| **opencode-workspace** | Multi-agent bundle | *(plugin config)* | Researcher, coder, scribe, reviewer |
| **@tarquinen/opencode-dcp** | Context pruning | `dcp.jsonc` | Auto-compress when context fills |

### Layer Architecture

```
┌─────────────────────────────────────────┐
│  Strategy Layer                         │
│  Alan Turing / Grace Hopper / Ada L.    │
│  High-level orchestration & delegation  │
├─────────────────────────────────────────┤
│  Specialist Layer                       │
│  workspace researcher/reviewer          │
│  oh-my-openagent Sisyphus/Oracle        │
├─────────────────────────────────────────┤
│  Memory Layer                           │
│  opencode-mem + DCP pruning             │
│  Persistent context + automatic trim    │
└─────────────────────────────────────────┘
```

---

## 📊 Session Usage Analyzer

Para analisar consumo de tokens da sessão atual, use a skill `session-usage-analyzer`:

```bash
# Dentro do opencode ou Claude Code
/session-usage-analyzer
```

O workflow Python está em `workflows/session-usage-analyzer.py`.

---

## 📖 Documentation Types

This repo uses three distinct documentation formats, each answering a different question:

| Type | Question | Location | Example |
|------|----------|----------|---------|
| **MADR** | *Why* did we decide X? | `docs/madr/` | "Why Bash+SQLite for token tracking?" |
| **Handbook** | *How* does Y work? | `docs/handbook/` + `docs/handbooks/` | "How does DCP pruning work?" |
| **Runbook** | *What to do when* Z happens? | `docs/runbooks/` | "Dashboard is empty — follow these steps" |

### When to use which

- **MADR** — Any technical decision with trade-offs that affects multiple components
- **Handbook** — Reference material someone reads to *understand* a system
- **Runbook** — Step-by-step procedure someone *follows* to execute a task or respond to an incident

---

## 🛠 CLI (`ocx`)

Todas as operações são via o comando `ocx` (Python CLI instalado com `uv`):

| Comando | Propósito |
|---------|-----------|
| `ocx setup` | Setup inicial: instala agents, sincroniza primários |
| `ocx agents sync` | Sincroniza primários para `~/.claude/agents/` |
| `ocx agents install [path]` | Instala agents em um projeto |
| `ocx agents count` | Conta agents instalados |
| `ocx shortcuts install` | Instala aliases de shell (oc, ocw, ocwserve) |
| `ocx litellm up/down/logs` | Gerencia o proxy LiteLLM |
| `ocx litellm status/models` | Health check e lista de modelos |
| `ocx litellm setup [--claude-code]` | Setup completo ou só Claude Code |
| `ocx tier list` | Lista os perfis de tier disponíveis |
| `ocx tier set <name>` | Aplica um tier (reescreve oh-my-openagent + litellm config) |
| `ocx tier show <name>` | Mostra os modelos do tier |
| `ocx tier diff <a> <b>` | Compara dois tiers lado a lado |
| `ocx tier current` | Mostra o tier ativo |
| `ocx configs check` | Verifica arquivos de config |
| `ocx git status` | Status git deste repo |

Veja `oc --help` para todos os subcomandos.

### Instalação e manutenção do CLI

```bash
# Instalar (primeira vez)
cd ~/.config/opencode
uv tool install --editable .

# Reinstalar após mudanças no pyproject.toml (novas dependências)
uv tool install --editable . --reinstall

# Verificar instalação
uv tool list          # mostra: ocx v1.0.0
which oc              # ~/.local/bin/oc

# Desinstalar
uv tool uninstall ocx
```

O `--editable` faz com que edições em `src/ocx/` tenham efeito imediato sem reinstalar.
O PATH é configurado automaticamente via `~/.local/bin/env` (sourced no `.zshrc`/`.bashrc`).

> **Conflito com alias**: Se `oc` ainda abrir o opencode TUI, você tem `alias oc="opencode"` no shell.
> Remova o alias ou use `alias op="opencode"` e libere `oc` para o CLI Python.

---

## ⚙️ Configuration Files

| File | Purpose | Tracked |
|------|---------|---------|
| `opencode.jsonc` | Main OpenCode config (plugins, permissions, MCP) | ✅ |
| `oh-my-openagent.jsonc` | Model configs, agent assignments, hooks | ✅ |
| `opencode-mem.jsonc` | Persistent memory config | ✅ |
| `dcp.jsonc` | Dynamic Context Pruning config | ❌ (generated) |
| `agents/*.md` | 191 agent definitions | ❌ (installed) |
| `agents/alan-turing.md` etc. | 5 primary orchestrators | ✅ (tracked exceptions) |

---

## 🔧 Shell Script Style Guide

All scripts in this repo follow consistent conventions (detailed in [AGENTS.md](./AGENTS.md)):

- **Safety**: `set -euo pipefail` on every script
- **Logging**: Colored helpers (`info`, `warn`, `error`) — never raw `echo`
- **Temp dirs**: `mktemp -d` with `trap 'rm -rf "$TMP"' EXIT`
- **Variables**: `UPPER_SNAKE_CASE`, quoted expansions (`"$VAR"`, `"${VAR:-default}"`)
- **Conditionals**: `[[ ... ]]` (not `[ ... ]`)
- **Directory changes**: Subshells `(cd "$DIR" && command)` to avoid side effects

---

## 🧪 Testing & Linting

- **No tests** — This is a configuration/agent-definition repository with no application logic
- **No linter** — Shell scripts follow the style guide above; do not add linting tooling without explicit instruction
- **Package manager**: Bun (`bun.lock` present, but `node_modules/` is gitignored)

---

## 📜 Agent Definition Format

Agents are Markdown files with YAML frontmatter:

```yaml
---
name: Human Readable Name
description: One-line description of role and specialty.
mode: subagent          # or "primary" for orchestrators
color: '#hexcolor'
---
```

Body follows a consistent section order:

```markdown
## 🧠 Your Identity & Memory
## 🎯 Your Core Mission
## 🚨 Critical Rules
## 🔄 Learning & Memory
## 🚀 Advanced Capabilities
```

See [AGENTS.md](./AGENTS.md) for the complete style guide.

---

## 🚫 What NOT to Commit

The following are **gitignored** and must never be manually added:

- `agents/` (except the 5 tracked primary agents)
- `.opencode/` (runtime directory)
- `.cursor/` (auto-generated Cursor rules)
- `node_modules/`, `package.json`, `bun.lock`
- `token-dashboard.html` (generated output)
- `token-baselines/` (personal snapshots)
- `dcp.jsonc` (generated by plugin installer)

---

## 📚 Further Reading

- **[AGENTS.md](./AGENTS.md)** — Complete agent guidance, style guides, and coexistence rules
- **[docs/handbook/README.md](./docs/handbook/README.md)** — Plugin documentation index
- **[docs/handbooks/token-tracker.md](./docs/handbooks/token-tracker.md)** — Token dashboard reference
- **[docs/madr/README.md](./docs/madr/README.md)** — Architecture decision records
- **[docs/runbooks/README.md](./docs/runbooks/README.md)** — Operational procedures index

---

## 🗺️ Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                      USER                                     │
│  "Build a feature" / "Fix this bug" / "Analyze this"        │
└──────────────────────┬───────────────────────────────────────┘
                       │
          ┌────────────┼────────────────┐
          ▼            ▼                ▼
   ┌────────────┐ ┌──────────┐ ┌──────────────┐
   │ Alan Turing │ │ Grace H. │ │ Ada Lovelace  │
   │  (SDLC)     │ │(Trouble) │ │ (Explore)     │
   └──────┬─────┘ └────┬─────┘ └──────┬───────┘
          │            │              │
          ▼            ▼              ▼
   ┌──────────────────────────────────────────┐
   │         AGENCY-AGENTS (191)              │
   │  backend-architect, security-engineer,   │
   │  sre, code-reviewer, api-tester, ...     │
   └──────────────────────────────────────────┘
          │            │              │
          ▼            ▼              ▼
   ┌──────────────────────────────────────────┐
    │           PLUGIN LAYER                     │
    │  opencode-mem │ DCP │ workspace             │
   └──────────────────────────────────────────┘
          │
          ▼
   ┌──────────────────────────────────────────┐
   │         OPENCODE (opencode.ai)            │
   │  CLI │ SQLite DB │ Token Tracking         │
   └──────────────────────────────────────────┘
```

---

*This repo is a living configuration — agents evolve, plugins update, and dashboards refresh. When in doubt, check the [runbooks](./docs/runbooks/) or [MADRs](./docs/madr/).*
# AGENTS.md — opencode Global Configuration Repository

This file provides guidance for AI coding agents operating in this repository.

---

## Repository Overview

This is the **global opencode configuration directory** (`~/.config/opencode`), not an application codebase.
Its purpose is to define and distribute AI sub-agent personas for the [opencode](https://opencode.ai) CLI,
and to mirror those agents to `~/.claude/agents/` for Claude Code compatibility.

**Tracked files** (only these are in git):
- `opencode.jsonc` — global opencode config (note: `.jsonc`, not `.json`)
- `src/ocx/` — Python CLI package (`oc` command, replaces all bash scripts)
- `pyproject.toml` — Python package definition for the `ocx` CLI
- `AGENTS.md` — this file
- `agents/` — all 84 agent `.md` files are tracked (all committed, not gitignored)
- `skills/` — team-shareable skill definitions (all tracked)

**Gitignored** (do not commit):
- `.opencode/` — runtime opencode directory
- `.cursor/` — Cursor IDE rule files
- `node_modules/`, `package.json`, `bun.lock`

> **Common mistake:** `AGENTS.md` and the README previously described `agents/` as gitignored. It is NOT.
> All 84 agent files are tracked in git. The `.gitignore` only excludes `.opencode/`, `.cursor/`, and `node_modules/`.

---

## Commands

The `ocx` CLI is the single entry point for all operations. Install it with `uv`:

```bash
cd ~/.config/opencode
uv tool install --editable .
```

Then use `ocx --help` to see all subcommands.

### Como o `uv tool` funciona

`uv tool install --editable .` instala o pacote definido em `pyproject.toml` como uma ferramenta global:

- O binário `oc` fica em `~/.local/bin/oc` (adicionado ao PATH pelo `~/.local/bin/env`, sourced no `.bashrc`/`.zshrc`)
- O `--editable` significa que edições em `src/ocx/` têm efeito imediato — não precisa reinstalar
- Para atualizar após mudanças no `pyproject.toml` (novas deps): `uv tool install --editable . --reinstall`
- Para verificar a instalação: `uv tool list` e `which oc`
- Para desinstalar: `uv tool uninstall oc`

O ambiente isolado da tool fica em `~/.local/share/uv/tools/oc/`. Não interfere com o `.venv` do projeto (usado para `uv run pytest`).

### Setup (run once per machine)

```bash
ocx setup
```

Clones [agency-agents](https://github.com/msitarzewski/agency-agents), converts agents to opencode
format, copies them to `~/.config/opencode/agents/`, then syncs primary agents to Claude Code.

### Sync primary agents to Claude Code

```bash
ocx agents sync
```

Strips `mode` and `permission` frontmatter fields (not supported by Claude Code) and copies these files
to `~/.claude/agents/`:
- `alan-turing.md`, `grace-hopper.md`, `tony-hoare.md`, `ada-lovelace.md`, `margaret-hamilton.md`, `agents-orchestrator.md`

**Source of truth:** `~/.config/opencode/agents/*.md`
**Claude Code mirror:** `~/.claude/agents/*.md` — do not edit directly

Run after editing any primary agent file.

### Per-project Agent Installation

```bash
# From inside a project root:
ocx agents install

# With explicit target:
ocx agents install /path/to/project
```

Installs agents to `<target>/.opencode/agents/`. Exits with a warning if the directory already exists.

### LiteLLM proxy

```bash
ocx litellm up          # start proxy
ocx litellm down        # stop proxy
ocx litellm logs        # tail logs
ocx litellm status      # health check
ocx litellm models      # list available models
ocx litellm env-init    # create litellm/.env from .env.example
ocx litellm setup       # full first-time setup
ocx litellm setup --claude-code  # only generate virtual key + configure Claude Code
```

### Other utilities

```bash
ocx agents count        # count installed agents
ocx configs check       # verify opencode config files exist
ocx git status          # git status of this repo
ocx shortcuts install   # install oc/ocw/ocwserve aliases into shell config
```

### Tests

```bash
uv run pytest          # run the test suite
```

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

> **Nota sobre `oh-my-openagent.jsonc`**: os blocos `agents` e `categories` mapeiam agents para modelos z.ai via LiteLLM proxy. Para que o roteamento funcione, o proxy deve estar rodando: `ocx litellm up`.

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

### Skill Sync — Convenção `tool:`

Todo `SKILL.md` pode ter um campo `tool:` no frontmatter. O comando `ocx agents sync` usa esse campo para decidir o que copiar para `~/.claude/skills/`.

| Valor | Comportamento |
|---|---|
| `shared` (default, se ausente) | Copiado para `~/.claude/skills/` com transformações automáticas |
| `opencode-only` | Permanece só em opencode — não é copiado para o Claude |
| `claude-only` | Copiado para `~/.claude/skills/` sem transformações (já no dialeto Claude Code) |

**Transformações aplicadas em skills `shared`:**

| opencode | Claude Code |
|---|---|
| `Task tool` | `Agent tool` |
| `show_options` tool | `AskUserQuestion` tool |

**Source of truth:** `~/.config/opencode/skills/` — incluindo skills claude-only.

**DO NOT EDIT** os arquivos em `~/.claude/skills/` diretamente — são sobrescritos pelo sync.  
Use `ocx agents sync --check` para detectar drift antes de commitar.

**Escape hatch:** envolva conteúdo com `<!-- skip-sync -->` ... `<!-- /skip-sync -->` para preservar byte-a-byte durante o sync.

### Companion Skills (orchestrators primários)

Skills que carregam o framework completo de cada primary agent:

| Skill | Companion para | Invocação |
|---|---|---|
| `alan-turing` | `agents/alan-turing.md` | `/alan-turing` (opencode) |
| `grace-hopper` | `agents/grace-hopper.md` | `/grace-hopper` (opencode) |
| `ada-lovelace` | `agents/ada-lovelace.md` | `/ada-lovelace` (opencode) |
| `margaret-hamilton` | `agents/margaret-hamilton.md` | `/margaret-hamilton` (opencode) |

---

## Budget Tiers

Model assignments and budget caps are managed via `ocx tier`. Thirteen profiles are available in `tiers/`; the table below shows the most common five:

| Tier | Budget | Primary models | Use case |
|------|--------|----------------|----------|
| `free` | $0 | opencode-go only | Exploration, low-stakes tasks |
| `low` | ~$5/mo | opencode-go primary, zai for reasoning | Light daily usage |
| `med` | ~$20/mo | zai primary, opencode-go fallback | **Default — matches current config** |
| `high` | ~$50/mo | zai/glm-5.1 everywhere | High-quality reasoning |
| `max` | ~$200/mo | Anthropic Opus/Sonnet primary | Maximum quality |

### Workflow

```bash
ocx tier list                  # see all tiers + current marker
ocx tier diff free max         # compare model assignments side-by-side
ocx tier set low               # switch to low-cost blend
ocx tier set low --dry-run     # preview without writing
ocx tier current               # see active tier
```

**What changes on `ocx tier set <name>`:**
1. `oh-my-openagent.jsonc` — agents and categories blocks are fully replaced.
2. `litellm/config.yaml` — model_list is rebuilt; `general_settings.max_budget` is set.
3. `.tier-state.json` — records the active tier (gitignored).

After switching tiers, restart the proxy: `ocx litellm down && ocx litellm up`.

**Tier profiles** live in `tiers/<name>.yaml` — edit them to customize models per agent.
`oh-my-openagent.jsonc` and `litellm/config.yaml` are now generated artifacts; manual edits
to their `agents`/`categories`/`model_list` blocks will be overwritten on the next `ocx tier set`.

---

## Python CLI Style Guide

The `ocx` CLI lives in `src/ocx/`. All operations should follow these conventions:

- **Logging**: use `oc.log.info/warn/error/section` — never raw `print`
- **Subprocess**: use `oc.proc.run` / `oc.proc.stream` — never `os.system`
- **Paths**: use constants from `oc.paths` — never hardcode `~/.config/opencode` inline
- **Error exit**: `log.error(msg)` raises `typer.Exit(1)` automatically
- **Idempotency**: every write operation should check before acting and warn if already done

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

`mode: primary` is used only for the six primary agents above. Claude Code does not support `mode` or `permission` — `ocx agents sync` strips them automatically.

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

## Known Bugs & Limitations

### `/start-work` ignora model overrides configurados (oh-my-openagent ≥ 3.x)

**Sintoma:** Após `/start-work`, o agente `sisyphus` ou `atlas` usa o modelo padrão do plugin
(`anthropic/claude-opus-4-7`) em vez do modelo configurado em `oh-my-openagent.jsonc`.

**Causa:** O hook `start-work` injeta `output.message["agent"]` mas nunca `output.message["model"]`.
O override de agente só é aplicado no startup da sessão, não em trocas mid-session.

**Workaround:** Após `/start-work`, trocar o modelo manualmente na UI antes de continuar.
Bug presente na v3.17.5 e v4.0.0. Detalhes completos: [`docs/runbooks/rb-010-start-work-model-override-bug.md`](docs/runbooks/rb-010-start-work-model-override-bug.md)

---

## Important Notes for Agents

- **Do not commit** `.opencode/`, `.cursor/`, `node_modules/`, `package.json`, `bun.lock`
- **`agents/` IS tracked** — all 84 files are in git; do not treat them as gitignored
- **Do not edit** `~/.claude/agents/*.md` directly — they are mirrors generated by `ocx agents sync`
- **Do not modify** `opencode.jsonc` permission gates without explicit user approval
- **`maestro.md` does not exist** — the legacy orchestrator reference in older docs is stale; use `agents-orchestrator.md`
- The config file is `opencode.jsonc` (with `.jsonc` extension), not `opencode.json`

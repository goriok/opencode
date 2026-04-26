# opencode-workspace — Multi-Agent Orchestration Bundle

> Um bundle com 16 componentes que funcionam juntos como um harness de desenvolvimento completo.

## Overview

`opencode-workspace` é um **bundle** — uma coleção curada de 16 componentes que trabalham juntos como um harness de desenvolvimento AI completo.

Ele inclui:
- 4 plugins principais
- 2 npm plugins
- 3 MCP servers
- 4 agentes especializados
- 4 skills
- 1 comando slash

## Componentes por Categoria

| Categoria | Componente | Descrição |
|-----------|------------|----------|
| Plugin | workspace-plugin | Plan management, agent rule injection |
| Plugin | background-agents | Sistema de delegação assíncrona |
| Plugin | notify | Notificações OS ao completar |
| Plugin | worktree | Isolamento com git worktrees |
| Plugin | @tarquinen/opencode-dcp | Differential Context Protocol |
| Plugin | @franlol/opencode-md-table-formatter | Formatador de tabelas markdown |
| Skill | plan-protocol | Guidelines de implementação |
| Skill | code-review | Metodologia + classificação |
| Skill | code-philosophy | Filosofia interna (5 Leis) |
| Skill | frontend-philosophy | Filosofia visual (5 Pilares) |
| Agent | researcher | Pesquisa externa (MCP, read-only) |
| Agent | coder | Implementação (full file + bash) |
| Agent | scribe | Documentação (write, no bash) |
| Agent | reviewer | Code review (read-only + git) |
| Command | review | `/review` slash command |
| MCP | context7 | Lookup de documentação |
| MCP | exa | Web search |
| MCP | gh_grep | GitHub code search |

## Installation

```json
{
  "plugin": ["opencode-workspace"]
}
```

Ou via CLI:

```bash
ocx add kdco/workspace --from https://registry.kdco.dev
```

## Configuration

### Configuração Principal

Crie `~/.config/opencode/opencode-workspace.jsonc`:

```json
{
  "plugins": {
    "workspace": {
      "enabled": true
    },
    "background": {
      "enabled": true,
      "max_parallel": 3
    },
    "notify": {
      "enabled": true,
      "sound": true
    },
    "worktree": {
      "default_base": "main"
    }
  },
  
  "agents": {
    "researcher": { "model": "claude-haiku" },
    "coder": { "model": "claude-sonnet" },
    "scribe": { "model": "claude-haiku" },
    "reviewer": { "model": "claude-opus" }
  },
  
  "mcp": {
    "context7": { "enabled": true },
    "exa": { "enabled": true },
    "gh_grep": { "enabled": true }
  }
}
```

### Werkree Config

Crie `~/.config/opencode/opencode-worktree.jsonc`:

```json
{
  "default_base": "main",
  "auto_cleanup": true,
  "auto_commit": true
}
```

## Agentes Especializados

### 🔍 Researcher

Pesquisa externa usando MCPs:

- **Ferramentas**: websearch, context7, grep_app (Apenas Leitura)
- **Modelo**: Haiku (rápido)
- **Permissões**: webfetch, mcp

### 💻 Coder

Agente de implementação:

- **Ferramentas**: arquivo completo + bash
- **Modelo**: Sonnet (balanceado)
- **Permissões**: edit, bash, read

### ✍️ Scribe

Documentação:

- **Ferramentas**: write (não bash)
- **Modelo**: Haiku
- **Permissões**: write (read-only para bash)

### 👀 Reviewer

Code review:

- **Ferramentas**: read-only + git
- **Modelo**: Opus (mais capaz)
- **Permissões**: read, git

## Skills Incluídas

### plan-protocol

Guidelines para implementação estruturada:

- Definição de escopo
- Breakdown em tasks
- Critérios de aceite
- Verificação final

### code-review

Metodologia de review:

- **Severity Classification**:
  - 🔴 Blocker — Não pode merge
  - 🟡 Suggestion — Melhoria opcional
  - 💭 Nit — Estilo/personal preference

- **Areas**:
  - Correctness
  - Security
  - Performance
  - Readability
  - Testing

### code-philosophy

5 Leis da lógica interna:

1. **Law of Least Surprise** — Código óbvio
2. **Law of Locality** — Cohesão
3. **Law of Narrowing** — Tipos específicos
4. **Law of Immutable First** — Imutável优先
5. **Law of Explicit Error** — Erros explícitos

### frontend-philosophy

5 Pilares visuais/UI:

1. **Clarity** — Clareza
2. **Consistency** — Consistência
3. **Feedback** — Resposta visual
4. **Hierarchy** — Hierarquia
5. **Accessibility** — Acessibilidade

## Plugins Incluídos

### workspace-plugin

Gerenciamento de plano + injeção de regras:

- Planeja implementação em fases
- Injeta regras do projeto
- Track progress

### background-agents

Execução assíncrona de agentes:

```typescript
// Delegates agentes sem bloquear
await task({
  agent: 'researcher',
  prompt: 'Find patterns for auth'
})

await task({
  agent: 'coder', 
  prompt: 'Implement the feature'
})
```

### notify

Notificações OS:

- Completion de tasks
- Erros
- Alerts

### worktree

Git worktrees isolados:

| Tool | Descrição |
|------|----------|
| `worktree_create(branch, baseBranch?)` | Cria worktree isolado |
| `worktree_delete(reason)` | Deleta worktree atual |

Suporte multiterminal:

| Platform | Terminais Suportados |
|----------|---------------------|
| macOS | Ghostty, iTerm2, Kitty, WezTerm, Alacritty, Warp |
| Linux | Kitty, WezTerm, Alacritty, GNOME Terminal, Konsole |
| Windows | Windows Terminal, cmd.exe |

### Differential Context Protocol (DCP)

Gerencia contexto de forma diferencial:

- Mantém apenas mudanças relevantes
- Compressão inteligente
- History preservation

### Markdown Table Formatter

Formatador de tabelas markdown:

```markdown
| Col1 | Col2 |
|------|------|
| Val1 | Val2 |
```

## MCPs Incluídos

### context7

Busca documentação oficial:

```
How to use React useState?
```

### exa

Web search:

```
Latest AI news 2026
```

### gh_grep

Busca código em GitHub:

```
useState loading example
```

## Comando /review

Slash command para code review:

```bash
/review
# ou
/review --files src/**/*.ts
```

Fluxo:
1. Analisa arquivos modificados
2. Aplica metodologia de review
3. Classifica findings por severity
4. Suggest correções

## Permission Boundaries

O bundle define permissões específicas:

| Agent | webfetch | edit | bash | agent |
|-------|----------|------|------|-------|
| researcher | ✅ | ❌ | ❌ | ✅ |
| coder | ❌ | ✅ | ✅ | ❌ |
| scribe | ❌ | ✅ | ❌ | ❌ |
| reviewer | ❌ | ❌ | ❌ | ✅ |

## Repositório

- GitHub: https://github.com/kdcokenny/opencode-workspace
- Registry: https://registry.kdco.dev
- npm: https://www.npmjs.com/package/opencode-workspace

---

*Parte do handbook de plugins OpenCode*
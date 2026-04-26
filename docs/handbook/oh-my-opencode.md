# oh-my-opencode — The #1 OpenCode Plugin

> Battery included. Steroids for your OpenCode.

## Overview

`oh-my-opencode` é oplugin mais popular para OpenCode. Ele traz:
- Async subagentes (como Claude Code)
- Agentes especializados com modelos apropriados
- Ferramentas LSP/AST integradas
- MCPs curados
- Camada de compatibilidade Claude Code

## Core Features

| Categoria | Feature | Descrição |
|-----------|---------|----------|
| 🤖 | **Async Subagentes** | Execute múltiplos agentes em background como uma equipe real |
| 👥 | **Agentes Especializados** | Sisyphus, Prometheus, Oracle, Librarian, Explore, Multimodal |
| 🛠️ | **LSP + AST-Grep** | Renomear em nível de workspace, diagnósticos, reesrita baseada em AST |
| 📚 | **MCPs Built-in** | Exa (websearch), Context7 (docs), Grep.app (GitHub search) |
| 🎯 | **Skills Embutidas** | Playwright, git-master, refactor, etc. |
| 🖥️ | **Claude Code Compat** | Hooks, comandos, skills, MCPs existentes funcionam |
| ⚡ | **Ultrawork Mode** | Execução paralela de máxima intensidade |

## Installation

```json
{
  "plugin": ["oh-my-opencode"]
}
```

## Configuration

Crie `~/.config/opencode/oh-my-opencode.jsonc`:

```json
{
  "disabled_hooks": [],
  "disabled_agents": [],
  "disabled_skills": [],
  "disabled_mcps": [],
  
  "model": {
    "default": { "provider": "anthropic", "model": "claude-sonnet-4-20250514" },
    "oracle": { "provider": "anthropic", "model": "claude-opus-4-5-20250514" },
    "librarian": { "provider": "anthropic", "model": "claude-haiku-4-5-20251001" }
  },
  
  "experimental": {
    "aggressive_truncation": false,
    "auto_resume": false
  },
  
  "hooks": {
    "thinking_block_validator": { "enabled": true }
  }
}
```

### Model Provider Configuration

Configure modelos por agente:

```json
{
  "model": {
    "default": { "provider": "openai", "model": "gpt-4o" },
    "oracle": { "provider": "anthropic", "model": "claude-opus-4" },
    "sisyphus": { "provider": "anthropic", "model": "claude-sonnet-4" }
  }
}
```

## Agentes Built-in

| Agente | Propósito | Modelo |
|--------|----------|--------|
| **Sisyphus** | Agente principal de orchestração | Sonnet |
| **Prometheus** | Planner de implementação | Haiku |
| **Oracle** | Arquitetura/debugging, Q&A | Opus |
| **Librarian** | Docs/code search | Haiku |
| **Explore** | Fast codebase grep | Haiku |
| **Multimodal** | Análise de mídia/imagens | Sonnet |

### Delegation por Domínio

| Domínio | Agente Recomendado |
|---------|------------------|
| `visual` | Frontend Developer |
| `business-logic` | Backend Architect |
| `research` | Researcher |
| `debug` | Oracle |

## Hooks do Sistema

20+ hooks automatizados:

### Workflow Hooks
- `directory-agents-injector` — Injeta AGENTS.md
- `directory-readme-injector` — Injeta README.md
- `rules-injector` — Injeta regras condicionais

### Output Management
- `grep-output-truncator` — Truncaoutput de grep
- `tool-output-truncator` — Trunca output de tools

### Code Quality
- `comment-checker` — Verifica comentários
- `thinking-block-validator` — Valida blocos de thinking

### Session Management
- `session-recovery` — Recupera sessões
- `session-notification` — Notificações de sessão
- `auto_resume` — Resume automático

### Context Management
- `context-window-monitor` — Monitora janela de contexto
- `compaction-context-injector` — Injeta contexto de compactação
- `preemptive-compaction` — Compactação preemptiva

### Task Management
- `todo-continuation-enforcer` — Impõecontinuação de TODOs
- `empty-task-response-detector` — Detecta respostas vazias

## MCPs Built-in

| MCP | Descrição | Enabled |
|-----|----------|----------|
| **Exa** | Web search | ✅ |
| **Context7** | Documentação oficial | ✅ |
| **Grep.app** | GitHub code search | ✅ |

### Context7

Busca documentação oficial de bibliotecas:

```
How do I use React useState hook?
```

### Exa

Web search para pesquisa externa:

```
Search for latest AI news 2026
```

### Grep.app

Busca código em milhões de repositórios públicos:

```
Find real useEffect cleanup examples
```

## LSP Support

Suporte completo a Language Server Protocol:

- Initialization options
- Environment configuration
- Extension mapping
- Priority management
- Custom LSP servers
- **Refactoring tools**: Rename, code actions
- Code analysis

## Skills Embutidas

| Skill | Descrição |
|-------|----------|
| `playwright` | Browser automation |
| `git-master` | Atomic commits, rebase |
| `refactor` | Refatoração inteligente |
| `code-review` | Review methodology |

## Comandos Slash

| Comando | Descrição |
|--------|----------|
| `/ultrawork` | Modo ultrawork (máxima intensidade) |
| `/ralph` | Loop Ralph |
| `/ultrawork-ralph` | combinados |
| `/ralph-cancel` | Cancela loops |
| `/think` | Ativa modo think |
| `/explain` | Explica código |
| `/review` | Review de código |

## Ultrawork Mode

Modo de execução de máxima intensidade:

```bash
# Ativar
/ultrawork

# Ou usar keywords no prompt
"ultrawork: implement X"
```

Features:
- Execução paralela de tasks
- Múltiplos agentes simultâneos
- Compressão agressiva de contexto

## Ralph Loop

Loop auto-referencial que continua atéverificação:

```
/ralph implement auth system
# Agente continua até完成任务
```

## Experimental Features

```json
{
  "experimental": {
    "aggressive_truncation": true,
    "auto_resume": true
  }
}
```

- **Aggressive Truncation**: Trunca outputs mais aggressive-
- **Auto Resume**: Resume sessões automaticamente

## Hooks Configuration

Desabilite hooks específicos:

```json
{
  "disabled_hooks": [
    "thinking_block_validator",
    "comment_checker"
  ]
}
```

## Repositório

- GitHub: https://github.com/opensoft/oh-my-opencode
- Site: https://ohmyopencode.com
- npm: https://www.npmjs.com/package/oh-my-opencode

---

*Parte do handbook de plugins OpenCode*
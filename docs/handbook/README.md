# OpenCode Plugins Handbook

> Documentação detalhada dos plugins instalados no ~/.config/opencode

## Plugins Instalados

| Plugin | Arquivo | Descrição |
|--------|--------|-----------|
| `opencode-mem` | [opencode-mem.md](./opencode-mem.md) | Memória persistente com vector database |
| `oh-my-openagent` | [oh-my-openagent.md](./oh-my-openagent.md) | Arsenal completo + hooks + ultrawork |
| `opencode-workspace` | [opencode-workspace.md](./opencode-workspace.md) | Multi-agent bundle (16 componentes) |
| **Conceitos** | [agent-sdk-conceitual.md](./agent-sdk-conceitual.md) | Agent SDK independente, deep research, multi-agent patterns |
| **Seus orquestradores** | [agents-coexistence.md](./agents-coexistence.md) | Alan Turing, Grace Hopper, Ada Lovelace |

## Agentes Orquestradores

| Seu Agente | Framework | Quando Usar |
|-----------|----------|------------|
| **Alan Turing** | SDLC | Features completos, projetos novos |
| **Grace Hopper** | Troubleshooting | Bugs, erros, incidentes |
| **Ada Lovelace** | ATAM | Análise, arquitetura, reviews |

## Configuração Atual

Local: `~/.config/opencode/opencode.jsonc`

```json
{
  "plugin": [
    "@tarquinen/opencode-dcp@latest",
    "opencode-mem",
    "oh-my-openagent",
    "opencode-workspace"
  ],
  "mcp": {
    "memory": { "enabled": false }
  }
}
```

## Arquivos de Configuração

| Arquivo | Propósito |
|--------|-----------|
| `opencode.jsonc` | Config principal |
| `dcp.jsonc` | Dynamic Context Pruning |
| `opencode-mem.jsonc` | Memória persistente |
| `oh-my-openagent.jsonc` | Model configs, hooks, ultrawork |

## Quick Reference

### opencode-mem
- **Funcionalidade**: Memória persistente
- **Features**: Vector DB, Web UI, Auto-capture
- **Porta**: 4747 (Web UI)
- **Config**: `~/.config/opencode/opencode-mem.jsonc`
- **Skill**: `/mem` command

### oh-my-openagent
- **Funcionalidade**: Arsenal completo
- **Features**: 20+ hooks, agents, MCPs, Ultrawork
- **Config**: `~/.config/opencode/oh-my-openagent.jsonc`
- **Commands**: `/ultrawork`, `/ralph`, `/review`

### opencode-workspace
- **Funcionalidade**: Bundle orchestration
- **Features**: 4 agents, 4 skills, 3 MCPs, /review command
- **Config**: `~/.config/opencode/opencode-workspace.jsonc`
- **Agents**: researcher, coder, scribe, reviewer

## Comparativo

| Característica | opencode-mem | oh-my-openagent | workspace |
|----------------|--------------|-----------------|-----------|
| **Memory** | ✅ Vector DB | ❌ | ❌ |
| **Agents** | ❌ | ✅ 6+ | ✅ 4 |
| **MCPs** | ❌ | ✅ 3 built-in | ✅ 3 |
| **Hooks** | ❌ | ✅ 20+ | ❌ |
| **Worktree** | ❌ | ❌ | ✅ |
| **Web UI** | ✅ | ❌ | ❌ |

## Recomendação de Uso

| Cenário | Plugin/Agente Recomendado |
|---------|-------------------|
| Lembrar de sessões anteriores | `opencode-mem` |
| Workflow completo | `oh-my-openagent` |
| Multi-agent orchestration | `opencode-workspace` |
| Feature completo (Requirements → Deploy) | **Alan Turing** |
| Bug / incidente | **Grace Hopper** |
| Análise / arquitetura | **Ada Lovelace** |
| **Tudo junto** | Use todos em harmonia! |

## Decision Tree

```
→ Novo feature?     → Alan Turing
→ Bug/incidente?   → Grace Hopper  
→ Análise/review?  → Ada Lovelace
→ Quick fix?       → oh-my-openagent
→ Lembrar contexto? → opencode-mem
```

## Roadmap

- [ ] Configurar todos os plugins
- [ ] Explorar MCPs do oh-my-openagent
- [ ] Verificar opencode-workspace agents

---

*Handbook criado em $(date)*
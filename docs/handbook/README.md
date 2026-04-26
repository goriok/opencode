# OpenCode Plugins Handbook

> Documentação detalhada dos plugins instalados no ~/.config/opencode

## Plugins Instalados

| Plugin | Arquivo | Descrição |
|--------|--------|-----------|
| `opencode-mem` | [opencode-mem.md](./opencode-mem.md) | Memória persistente com vector database |
| `oh-my-opencode` | [oh-my-opencode.md](./oh-my-opencode.md) | Battery included - Steroids |
| `opencode-workspace` | [opencode-workspace.md](./opencode-workspace.md) | Multi-agent bundle (16 componentes) |
| `micode` | [micode.md](./micode.md) | Workflow Brainstorm → Plan → Implement |

## Configuração Atual

Local: `~/.config/opencode/opencode.jsonc`

```json
{
  "plugin": [
    "@tarquinen/opencode-dcp@latest",
    "opencode-mem",
    "oh-my-opencode",
    "opencode-workspace",
    "micode"
  ]
}
```

## Quick Reference

### opencode-mem
- **Funcionalidade**: Memória persistente
- **Features**: Vector DB, Web UI, Auto-capture
- **Porta**: 4747 (Web UI)
- **Config**: `~/.config/opencode/opencode-mem.jsonc`

### oh-my-opencode
- **Funcionalidade**: Arsenal completo
- **Features**: 20+ hooks, agents, MCPs, Ultrawork
- **Config**: `~/.config/opencode/oh-my-opencode.jsonc`

### opencode-workspace
- **Funcionalidade**: Bundle orchestration
- **Features**: 4 agents, 4 skills, 3 MCPs, /review command
- **Config**: `~/.config/opencode/opencode-workspace.jsonc`

### micode
- **Funcionalidade**: Workflow estruturado
- **Features**: 3-stage lifecycle, TDD, worktrees
- **Config**: `~/.config/opencode/micode.jsonc`

## Comparativo

| Característica | opencode-mem | oh-my-opencode | workspace | micode |
|----------------|--------------|----------------|-----------|--------|
| **Memory** | ✅ Vector DB | ❌ | ❌ | ✅ Ledger |
| **Agents** | ❌ | ✅ 6+ | ✅ 4 | ✅ 12 |
| **MCPs** | ❌ | ✅ 3 built-in | ✅ 3 | ❌ |
| **Hooks** | ❌ | ✅ 20+ | ❌ | ❌ |
| **Worktree** | ❌ | ❌ | ✅ | ✅ |
| **TDD** | ❌ | ❌ | ❌ | ✅ |
| **Web UI** | ✅ | ❌ | ❌ | ❌ |

## Recomendação de Uso

| Cenário | Plugin Recomendado |
|---------|-------------------|
| Lembrar de sessões anteriores | `opencode-mem` |
| Workflow completo | `oh-my-opencode` |
| Multi-agent orchestration | `opencode-workspace` |
| TDD + estrutura | `micode` |
| **Tudo junto** | Use todos! |

## Roadmap

- [ ] Configurar todos os plugins
- [ ] Explorar MCPs do oh-my-opencode
- [ ] Testar micode workflow
- [ ] Verificar opencode-workspace agents

---

*Handbook criado em $(date)*
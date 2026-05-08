# RB-004 — Adicionar Agente Primário

**Quando usar**: Criar um novo agente orquestrador primário (como Alan Turing, Grace Hopper, Ada Lovelace).
**Tempo estimado**: 30-60 minutos
**Pré-requisitos**: Conhecer os frameworks do agente (ISO-25010, ATAM, RM-ODP)

## Passos

### 1. Criar arquivo do agente

Criar `~/.config/opencode/agents/nome-do-agente.md` com:

```markdown
---
name: Nome do Agente
description: Uma linha descrevendo o papel e especialidade.
mode: primary
color: '#hexcolor'
---

## 🧠 Your Identity & Memory
[Descrição da persona]

## 🎯 Your Core Mission
[Missão principal]

## 🚨 Critical Rules
[Regras obrigatórias]

## 🔄 Learning & Memory
[Como aprende e memoriza]

## 🚀 Advanced Capabilities
[Capacidades especiais]
```

### 2. Definir squad de subagentes

No corpo do agente, listar quais subagentes do agency-agents ele delega:

```markdown
### Squad
- `backend-architect` — Arquitetura de backend
- `security-engineer` — Segurança
- `sre` — Confiabilidade
```

### 3. Criar skill companion

Criar `~/.config/opencode/skills/nome-do-agente/SKILL.md`:

```markdown
---
description: Descrição curta da skill
---
[Instruções de invocação e workflow]
```

### 4. Registrar no opencode.jsonc

Adicionar o agente na seção de agentes (se aplicável).

### 5. Sincronizar para Claude Code

```bash
oc agents sync
```

### 6. Testar

```bash
# No OpenCode, invocar o agente
/nome-do-agente

# Verificar que aparece na lista
ls ~/.claude/agents/nome-do-agente.md
```

## Validação

- [ ] Arquivo `.md` existe em `~/.config/opencode/agents/`
- [ ] Skill existe em `~/.config/opencode/skills/`
- [ ] Agente aparece no OpenCode
- [ ] Copia em `~/.claude/agents/` após sync

## Troubleshooting

- **Agente não aparece**: Verificar frontmatter YAML
- **Skill não carrega**: Verificar campo `description` no SKILL.md
- **Sync falha**: Verificar se `oc` está instalado (`uv tool install --editable ~/.config/opencode`)
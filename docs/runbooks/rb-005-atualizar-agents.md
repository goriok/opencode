# RB-005 — Atualizar Agents do agency-agents

**Quando usar**: Nova versão do agency-agents disponível, ou agentes desatualizados.
**Tempo estimado**: 5-10 minutos
**Pré-requisitos**: Git, `oc` instalado

## Passos

### 1. Verificar versão atual

```bash
oc agents count
# Anotar o número
```

### 2. Rodar setup novamente

```bash
oc setup
```

Re-clona agency-agents e reinstala os agentes. Já sincroniza os primários automaticamente.

### 3. Validar

```bash
# Contar agentes
oc agents count

# Verificar que primários estão intactos
head -5 ~/.claude/agents/alan-turing.md
```

## Validação

- [ ] Número de agentes manteve ou aumentou
- [ ] Agentes primários sincronizados
- [ ] OpenCode carrega sem erros

## Troubleshooting

- **Setup falha**: `rm -rf ~/.config/opencode/agents/` e re-executar `oc setup`
- **Primários desapareceram**: Re-executar `oc agents sync`
- **Conflito de versão**: Verificar se agency-agents repo está atualizado
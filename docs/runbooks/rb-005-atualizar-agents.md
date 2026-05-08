# RB-005 — Atualizar Agents do agency-agents

**Quando usar**: Nova versão do agency-agents disponível, ou agentes desatualizados.
**Tempo estimado**: 5-10 minutos
**Pré-requisitos**: Git, `ocx` instalado

## Passos

### 1. Verificar versão atual

```bash
ocx agents count
# Anotar o número
```

### 2. Rodar setup novamente

```bash
ocx setup
```

Re-clona agency-agents e reinstala os agentes. Já sincroniza os primários automaticamente.

### 3. Validar

```bash
# Contar agentes
ocx agents count

# Verificar que primários estão intactos
head -5 ~/.claude/agents/alan-turing.md
```

## Validação

- [ ] Número de agentes manteve ou aumentou
- [ ] Agentes primários sincronizados
- [ ] OpenCode carrega sem erros

## Troubleshooting

- **Setup falha**: `rm -rf ~/.config/opencode/agents/` e re-executar `ocx setup`
- **Primários desapareceram**: Re-executar `ocx agents sync`
- **Conflito de versão**: Verificar se agency-agents repo está atualizado
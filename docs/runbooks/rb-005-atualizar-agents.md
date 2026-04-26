# RB-005 — Atualizar Agents do agency-agents

**Quando usar**: Nova versão do agency-agents disponível, ou agentes desatualizados.
**Tempo estimado**: 5-10 minutos
**Pré-requisitos**: Git, setup.sh já executado antes

## Passos

### 1. Verificar versão atual

```bash
ls ~/.config/opencode/agents/ | wc -l
# Anotar o número
```

### 2. Rodar setup novamente

```bash
bash ~/.config/opencode/setup.sh
```

O script detecta instalação existente e atualiza.

### 3. Verificar agentes primários

```bash
ls ~/.claude/agents/
# Deve ter: alan-turing.md, grace-hopper.md, ada-lovelace.md, maestro.md
```

### 4. Sincronizar primários

```bash
bash ~/.config/opencode/sync-primary-agents.sh
```

### 5. Validar

```bash
# Contar agentes
ls ~/.config/opencode/agents/ | wc -l

# Verificar que primários estão intactos
cat ~/.claude/agents/alan-turing.md | head -5
```

## Validação

- [ ] Número de agentes manteve ou aumentou
- [ ] Agentes primários sincronizados
- [ ] OpenCode carrega sem erros

## Troubleshooting

- **Setup falha**: `rm -rf ~/.config/opencode/agents/` e re-executar
- **Primários desapareceram**: Re-executar `sync-primary-agents.sh`
- **Conflito de versão**: Verificar se agency-agents repo está atualizado
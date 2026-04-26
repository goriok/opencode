# RB-002 — Gerar Dashboard de Tokens

**Quando usar**: Verificar uso de tokens, custo, eficiência de cache, ou comparar períodos.
**Tempo estimado**: 30 segundos
**Pré-requisitos**: OpenCode com dados no SQLite, `sqlite3` e `python3` instalados

## Passos

### Uso básico — Dashboard dos últimos 30 dias

```bash
bash ~/.config/opencode/token-tracker.sh --open
```

### Período customizado

```bash
# Últimos 7 dias
bash ~/.config/opencode/token-tracker.sh --days 7 --open

# Últimos 90 dias (visão macro)
bash ~/.config/opencode/token-tracker.sh --days 90 --open
```

### Stats rápidos no terminal (sem HTML)

```bash
bash ~/.config/opencode/token-tracker.sh --dry-run
bash ~/.config/opencode/token-tracker.sh --dry-run --days 7
```

### Salvar baseline para comparação futura

```bash
bash ~/.config/opencode/token-tracker.sh --baseline "pre-nova-estrategia" --days 30
```

### Comparar com baseline existente

```bash
bash ~/.config/opencode/token-tracker.sh --compare "pre-nova-estrategia" --days 30 --open
```

### Output customizado

```bash
bash ~/.config/opencode/token-tracker.sh --output ~/Desktop/dashboard.html --open
```

## Validação

- [ ] Dashboard abre no browser
- [ ] KPI cards mostram números (não zero)
- [ ] Gráficos renderizam com dados
- [ ] Tabelas são sortable ao clicar nos headers

## Troubleshooting

- **"OpenCode database not found"**: Verificar se `~/.local/share/opencode/opencode.db` existe
- **Dashboard abre vazio**: Ver RB-003
- **Baseline não encontrado**: Verificar `~/.config/opencode/token-baselines/`
- **Chart.js não carrega**: Verificar conexão com internet (CDN)
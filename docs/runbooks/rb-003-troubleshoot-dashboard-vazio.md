# RB-003 — Troubleshoot: Dashboard Vazio ou com Erros

**Quando usar**: Dashboard não mostra dados, gráficos vazios, ou erros ao gerar.
**Tempo estimado**: 5-10 minutos
**Pré-requisitos**: `token-tracker.sh` instalado

## Diagnóstico

### Passo 1: Verificar se o banco existe

```bash
ls -la ~/.local/share/opencode/opencode.db
```

Se não existe: OpenCode não foi usado ainda, ou está em outro path.

### Passo 2: Verificar se há dados

```bash
sqlite3 ~/.local/share/opencode/opencode.db \
  "SELECT COUNT(*) FROM message WHERE json_extract(data, '$.role') = 'assistant'"
```

Se retorna 0: Nenhuma mensagem de assistant. Use o OpenCode mais e tente novamente.

### Passo 3: Testar queries

```bash
bash ~/.config/opencode/token-tracker.sh --dry-run --days 30
```

Se mostra dados no terminal mas dashboard vazio: problema na geração do HTML.

### Passo 4: Verificar dependências

```bash
which sqlite3    # Deve retornar path
which python3   # Deve retornar path
```

Se ausente: `brew install sqlite3 python3`

### Passo 5: Verificar baseline corrompido

```bash
bash ~/.config/opencode/token-tracker.sh --validate
```

Se inválido: deletar e re-criar.

## Problemas Comuns

| Sintoma | Causa | Solução |
|---------|-------|---------|
| "OpenCode database not found" | DB não existe | Verificar path, usar OpenCode primeiro |
| Dashboard vazio | Sem dados no período | Aumentar `--days` ou usar o OpenCode mais |
| Chart.js não carrega | Sem internet | Vendorizar Chart.js ou conectar |
| Baseline inválido | JSON corrompido | Deletar `token-baselines/baseline-*.json` e re-criar |
| Números muito grandes | Mensagens sem tokens.total | Script já filtra (WHERE tokens.total IS NOT NULL) |
| Custo zero | Modelo sem custo rastreado | Verificar se `cost` está populado no JSON |

## Validação

- [ ] `--dry-run` mostra dados no terminal
- [ ] Dashboard abre com gráficos preenchidos
- [ ] KPI cards mostram valores > 0
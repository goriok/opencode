# Token Tracker — Handbook

> Dashboard de uso de tokens do OpenCode com baseline comparison para avaliação de estratégias de IA.

## O que é

O `token-tracker.sh` lê o banco SQLite do OpenCode (`~/.local/share/opencode/opencode.db`) e gera um dashboard HTML interativo com Chart.js. Permite visualizar tendências de uso de tokens, custo, eficiência de cache, e comparar períodos antes/depois de mudanças de estratégia.

## Arquitetura

```
opencode.db (SQLite) → token-tracker.sh → token-dashboard.html
                                ↓
                     token-baselines/*.json (snapshots)
```

**Princípio**: Dados já existem no SQLite. O script só lê e visualiza. Nunca modifica o banco.

## Comandos

| Comando | Descrição |
|---------|-----------|
| `bash token-tracker.sh` | Gera dashboard dos últimos 30 dias |
| `bash token-tracker.sh --days 7` | Últimos 7 dias |
| `bash token-tracker.sh --dry-run` | Stats no terminal, sem HTML |
| `bash token-tracker.sh --open` | Gera e abre no browser |
| `bash token-tracker.sh --baseline "nome"` | Salva snapshot com esse nome |
| `bash token-tracker.sh --compare "nome"` | Compara com baseline salvo |
| `bash token-tracker.sh --validate` | Valida baselines existentes |

## Métricas

### Primárias (baseline)

| Métrica | Fórmula | Significado |
|---------|---------|-------------|
| **Tokens/dia** | `SUM(tokens.total) / dias_ativos` | Volume total de processamento |
| **Cost/dia** | `SUM(cost) / dias_ativos` | Gasto diário em USD |
| **Sessões/dia** | `COUNT(DISTINCT session) / dias_ativos` | Atividade |

### Derivadas (eficiência)

| Métrica | Fórmula | Significado |
|---------|---------|-------------|
| **Cache Hit Rate** | `cache.read / tokens.total` | Quanto contexto é servido do cache vs reprocessado |
| **Output Ratio** | `tokens.output / tokens.total` | Quanto vira código útil vs overhead de contexto |
| **Cost/Output Token** | `cost / tokens.output` | Custo real por token de output |

### Comparativas (estratégia)

| Métrica | Fórmula | Significado |
|---------|---------|-------------|
| **Delta Tokens** | `(atual - baseline) / baseline` | Mudança percentual no volume |
| **Delta Cost** | `(atual - baseline) / baseline` | Mudança percentual no custo |
| **Delta Cache Hit** | `(atual - baseline) / baseline` | Melhoria ou piora no cache |

## Baselines

Baselines são snapshots JSON salvos em `~/.config/opencode/token-baselines/`. Cada snapshot contém:

- Métricas agregadas do período
- Breakdown por agente e modelo
- Dados diários completos

### Workflow típico

```bash
# 1. Antes de mudar estratégia, salve baseline
bash token-tracker.sh --baseline "pre-new-model" --days 30

# 2. Use a nova estratégia por um período

# 3. Compare resultados
bash token-tracker.sh --compare "pre-new-model" --days 30 --open
```

## Views do Dashboard

| Seção | Descrição |
|-------|-----------|
| **KPI Cards** | 8 métricas principais com deltas vs baseline |
| **Daily Timeline** | Gráfico de linhas: total, input, output, cache |
| **Cost Chart** | Barras de custo diário |
| **Cache Hit Rate** | Linha temporal de eficiência de cache |
| **Agent Breakdown** | Doughnut chart + tabela de eficiência |
| **Model Comparison** | Barras horizontais por modelo |
| **Agent Table** | Tabela sortable: msgs, tokens, output ratio, cache hit, cost |
| **Model Table** | Tabela sortable: msgs, tokens, cache hit, cost, $/1K output |
| **Session Table** | Tabela sortable: sessões recentes com métricas |

## Banco de Dados

**Localização**: `~/.local/share/opencode/opencode.db`

**Tabelas relevantes**:

| Tabela | Campos-chave |
|--------|-------------|
| `message` | `id`, `session_id`, `time_created`, `data` (JSON) |
| `session` | `id`, `parent_id`, `slug`, `title`, `time_created` |

**JSON em `message.data`**:

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `tokens.total` | int | Total de tokens processados |
| `tokens.input` | int | Tokens de entrada |
| `tokens.output` | int | Tokens de saída |
| `tokens.cache.read` | int | Tokens servidos do cache |
| `tokens.cache.write` | int | Tokens escritos no cache |
| `cost` | float | Custo em USD |
| `modelID` | string | Modelo usado |
| `agent` | string | Agente que processou |
| `mode` | string | Modo da sessão |

## Arquivos Gerados

| Arquivo | Localização | Gitignore |
|---------|-------------|-----------|
| Dashboard HTML | `~/.config/opencode/token-dashboard.html` | Sim |
| Baseline JSON | `~/.config/opencode/token-baselines/baseline-*.json` | Sim |
| Script | `~/.config/opencode/token-tracker.sh` | Não (tracked) |

## Dependências

- `sqlite3` — Leitura do banco
- `python3` — Processamento de JSON e formatação
- `bash` — Orquestração
- Browser com JavaScript — Visualização (Chart.js via CDN)
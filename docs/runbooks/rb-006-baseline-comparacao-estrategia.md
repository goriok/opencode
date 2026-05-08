# RB-006 — Comparar Estratégias com Baseline

> **⚠️ Depreciado**: O `token-tracker.sh` foi removido. Este runbook não se aplica mais.

**Status**: Descontinuado — `token_tracker` foi removido do repositório.

## Contexto

Esse runbook é para quando você mudou algo na sua estratégia de IA (trocou modelo, ajustou prompts, adicionou agente) e quer medir o impacto quantitativamente.

## Passos

### 1. Verificar baseline existente

```bash
ls ~/.config/opencode/token-baselines/
```

Deve haver pelo menos um arquivo `baseline-*.json`.

### 2. Validar baseline

```bash
bash ~/.config/opencode/token-tracker.sh --validate
```

Todos devem mostrar ✓.

### 3. Gerar dashboard com comparação

```bash
# Comparar com baseline específico
bash ~/.config/opencode/token-tracker.sh --compare "pre-nova-estrategia" --open

# Comparar com baseline dos últimos 30 dias
bash ~/.config/opencode/token-tracker.sh --compare "pre-nova-estrategia" --days 30 --open
```

### 4. Interpretar os resultados

No dashboard, os **KPI cards** mostram deltas (↑↓) vs baseline:

| Métrica | ↑ bom? | Significado |
|---------|--------|-------------|
| **Total Tokens** | Depende | Mais tokens = mais trabalho, mas pode ser desperdício |
| **Tracked Cost** | ❌ | Custo reportado pelos providers subiu = ruim (mas pode ser enganoso — veja abaixo) |
| **Est. API Cost** | ❌ | Custo estimado por API pricing subiu = ruim |
| **Cache Hit Rate** | ✅ | Mais cache = mais eficiência |
| **Output Ratio** | ✅ | Mais output vs input = mais eficiência |

### ⚠️ Entendendo Tracked Cost vs Est. API Cost

- **Tracked Cost** = o que os providers reportam (enganoso: Anthropic/Copilot reportam $0, opencode-go reporta por token mas assinatura é flat)
- **Est. API Cost** = o que esses tokens custariam se você pagasse por API (calculado com pricing tables publicadas)
- **O custo real que você paga é a assinatura flat**, não nenhum dos dois números acima
- Para comparação de estratégia, **Est. API Cost** é mais útil porque normaliza entre providers

### 5. Salvar novo baseline (opcional)

Se a nova estratégia se provou melhor, salve como novo baseline:

```bash
bash ~/.config/opencode/token-tracker.sh --baseline "pos-nova-estrategia" --days 30
```

## Exemplo Prático

### Cenário: Trocar de claude-sonnet-4.6 para glm-5.1

```bash
# Antes da troca (já devia ter sido feito)
# bash token-tracker.sh --baseline "pre-glm-migration"

# ... usar glm-5.1 por 1-2 semanas ...

# Depois
bash token-tracker.sh --compare "pre-glm-migration" --days 14 --open

# Resultado esperado:
# - Cache Hit Rate: pode mudar (glm tem contexto diferente)
# - Cost: provavelmente ↓ (glm-5.1 é mais barato)
# - Output Ratio: verificar se manteve ou melhorou
```

## Validação

- [ ] Baseline carrega sem erro
- [ ] Dashboard mostra deltas (↑↓) nos KPI cards
- [ ] Comparação é entre períodos equivalentes (mesmo nº de dias)

## Troubleshooting

- **"Baseline not found"**: Verificar nome exato em `token-baselines/`
- **Deltas mostram N/A**: Períodos não comparáveis (zero tokens no baseline)
- **Resultados inconsistentes**: Comparar mesmo # de dias, considerar dias sem atividade
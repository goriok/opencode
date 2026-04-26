# RB-007 — Iniciar e configurar o Prometheus exporter

**Quando usar**: Exportar metricas de uso de tokens para Prometheus/Grafana
**Tempo estimado**: 5 minutos
**Pre-requisitos**: Python 3.9+, `prometheus-client` instalado

## Passos

### 1. Instalar dependencia

```bash
pip install "prometheus-client>=0.19,<1.0"
```

### 2. Iniciar o exporter

```bash
# Porta padrao (9090)
python3 -m token_tracker servemetrics

# Porta customizada (evitar conflito com Prometheus local)
python3 -m token_tracker servemetrics --port 9099 --host localhost --days 30
```

O exporter coleta os dados uma vez no startup e mantem as metricas em memoria.

### 3. Configurar Prometheus

Adicione o job ao `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'opencode-tokens'
    static_configs:
      - targets: ['localhost:9090']
    scrape_interval: 1h
```

### 4. Verificar metricas

```bash
curl -s http://localhost:9090/metrics | grep opencode_
```

Saida esperada (exemplo):

```
# HELP opencode_tokens_total Total tokens consumed per source and model
# TYPE opencode_tokens_total gauge
opencode_tokens_total{model="deepseek-v4",source="opencode"} 5000.0
opencode_tokens_total{model="claude-sonnet-4-6",source="claude_code"} 2500.0
# HELP opencode_cost_tracked_total Tracked (recorded) cost per source and model
# TYPE opencode_cost_tracked_total gauge
...
# HELP opencode_messages_total Total assistant messages per source
# TYPE opencode_messages_total gauge
opencode_messages_total{source="opencode"} 42.0
opencode_messages_total{source="claude_code"} 15.0
```

### 5. Criar dashboard no Grafana (opcional)

1. Adicione o Prometheus como data source no Grafana
2. Crie um novo dashboard com os seguintes paineis:

| Painel | Query PromQL |
|--------|-------------|
| Tokens por modelo | `opencode_tokens_total` |
| Custo total | `sum(opencode_cost_estimated_total)` |
| Cache hit rate | `sum(opencode_tokens_total{model!=""}) / ...` |
| Mensagens/dia | `opencode_messages_total` |

## Validacao

- [ ] `pip install prometheus-client` concluido sem erros
- [ ] `python3 -m token_tracker servemetrics` inicia sem crash
- [ ] `curl localhost:9090/metrics` retorna 4 metricas `opencode_*`
- [ ] Prometheus scrape config registra o target como UP

## Troubleshooting

### "Address already in use"

A porta 9090 ja esta em uso (provavelmente pelo Prometheus local).

```bash
# Usar porta alternativa
python3 -m token_tracker servemetrics --port 9099
```

E atualizar o `prometheus.yml` com a nova porta.

### "No module named 'prometheus_client'"

```bash
pip install "prometheus-client>=0.19,<1.0"
```

### "No data sources found" / metricas vazias

O exporter nao encontrou banco de dados do OpenCode ou diretorio do Claude Code.
Verifique se os paths padrao existem:
- OpenCode: `~/.local/share/opencode/opencode.db`
- Claude Code: `~/.claude/projects/`

### Metricas nao atualizam

Os dados sao coletados apenas no startup. Reinicie o processo para atualizar:

```bash
# Parar (Ctrl+C) e reiniciar
python3 -m token_tracker servemetrics --days 30
```

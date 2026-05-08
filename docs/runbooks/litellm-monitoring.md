# LiteLLM Monitoring Guide

> Monitoramento completo do LiteLLM Proxy com Prometheus e Dashboard built-in.

---

## ✅ Status Atual

| Componente | Status | Endpoint |
|------------|--------|----------|
| Prometheus Metrics | ✅ Funcionando | `http://localhost:4000/metrics` |
| Built-in Dashboard | ✅ Funcionando | `http://localhost:4000/ui` |
| Redis Cache | ✅ Funcionando | `redis:6379` |
| Grafana | ⏳ Configuração manual | - |

---

## 1. Prometheus Metrics

### Endpoint

```bash
curl -sL http://localhost:4000/metrics | head -100
```

### Métricas Disponíveis

#### Proxy Metrics
```prometheus
litellm_proxy_total_requests_metric_total{requested_model="..."}
litellm_proxy_failed_requests_metric_total
litellm_proxy_total_requests_metric_created
```

#### Latência Metrics
```prometheus
litellm_request_total_latency_metric_bucket{model="...", le="0.005"}
litellm_llm_api_latency_metric_bucket
litellm_llm_api_time_to_first_token_metric_bucket
```

#### System Metrics
```prometheus
process_virtual_memory_bytes
process_resident_memory_bytes
process_cpu_seconds_total
process_open_fds
python_gc_objects_collected_total
```

### Labels Disponíveis

- `requested_model` - Modelo solicitado (ex: `zai/glm-5.1`)
- `model` - Modelo real (ex: `glm-5.1`)
- `hashed_api_key` - API key hash
- `status_code` - HTTP status code
- `route` - Endpoint chamado
- `client_ip` - IP do cliente
- `user_agent` - User-Agent da request

---

## 2. Built-in Dashboard

### Acesso

```
URL: http://localhost:4000/ui
Auth: LITELLM_MASTER_KEY (verificar em litellm/.env)
```

### Recursos

- Cache hit rate
- Costos por modelo
- Latência por request
- Error rate
- Activity logs detalhados
- Model performance comparison

---

## 3. Prometheus Scrape Config

### Adicionar ao `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'litellm'
    metrics_path: "/metrics"
    static_configs:
      - targets: ['localhost:4000']
    scrape_interval: 15s
```

### Restart Prometheus

```bash
kill -HUP $(pidof prometheus)
# ou
systemctl restart prometheus
```

### Verificar Targets

```
http://localhost:9090/targets
```

---

## 4. Grafana Dashboard

### Importar Dashboard Oficial

1. Acessar: http://localhost:3000
2. Import dashboard: ID `24965`
3. URL: https://grafana.com/grafana/dashboards/24965-litellm/

### Queries Úteis

#### Requests por Minuto
```promql
rate(litellm_proxy_total_requests_metric_total[5m])
```

#### Latência P95
```promql
histogram_quantile(0.95,
  rate(litellm_request_total_latency_metric_bucket[5m])
)
```

#### Error Rate
```promql
rate(litellm_proxy_failed_requests_metric_total[5m]) /
rate(litellm_proxy_total_requests_metric_total[5m])
```

#### Cache Hit Rate (via Redis)
```bash
curl -s http://localhost:4000/cache/ping -H "Authorization: Bearer $LITELLM_MASTER_KEY"
```

---

## 5. Alertas Recomendados

### Alta Latência
```yaml
- alert: HighLatency
  expr: histogram_quantile(0.95, rate(litellm_request_total_latency_metric_bucket[5m])) > 30
  for: 5m
  annotations:
    summary: "P95 latency > 30s"
```

### High Error Rate
```yaml
- alert: HighErrorRate
  expr: rate(litellm_proxy_failed_requests_metric_total[5m]) / rate(litellm_proxy_total_requests_metric_total[5m]) > 0.05
  for: 5m
  annotations:
    summary: "Error rate > 5%"
```

### Request Spike
```yaml
- alert: RequestSpike
  expr: rate(litellm_proxy_total_requests_metric_total[1m]) > 100
  for: 2m
  annotations:
    summary: "> 100 req/s detected"
```

---

## 6. Configuração Atual

### `litellm/config.yaml`

```yaml
litellm_settings:
  # ─── Metrics & Monitoring ──────────────────────────────────────────────────
  callbacks:
    - prometheus

  # ─── Redis Cache ──────────────────────────────────────────────────────────
  cache: true
  cache_params:
    type: redis
    host: os.environ/REDIS_HOST
    port: 6379
    namespace: "litellm.cache"
    ttl: 600
    max_connections: 50
  enable_redis_auth_cache: true

  # ─── General ──────────────────────────────────────────────────────────────
  drop_params:
    - reasoningSummary
  request_timeout: 120
  num_retries: 0
```

### Variáveis de Ambiente

```bash
# No docker-compose.yml
REDIS_HOST: redis
LITELLM_MASTER_KEY: sk-litellm-local
ZAI_API_KEY: <your-key>
```

---

## 7. Troubleshooting

### Metrics não aparecendo?

```bash
# Verificar se Prometheus callback está ativo
docker compose logs litellm | grep -i prometheus

# Testar endpoint direto
curl -sL http://localhost:4000/metrics | grep litellm
```

### Dashboard não acessível?

```bash
# Verificar master key
cat litellm/.env | grep LITELLM_MASTER_KEY

# Testar health check
curl http://localhost:4000/health
```

### Redis cache não funciona?

```bash
# Verificar Redis
docker exec litellm-redis-1 redis-cli ping

# Testar cache
curl -s http://localhost:4000/cache/ping -H "Authorization: Bearer $LITELLM_MASTER_KEY"
```

---

## 8. Próximos Passos Opcionais

- [ ] Configurar Prometheus persistente
- [ ] Adicionar alertas no Alertmanager
- [ ] Configurar OpenTelemetry para tracing
- [ ] Integrar com ferramenta de logging (Loki/ELK)
- [ ] Configurar backup do Redis AOF

---

## Referências

- [LiteLLM Prometheus Docs](https://litellm.vercel.app/docs/proxy/prometheus)
- [Grafana Dashboard Oficial](https://grafana.com/grafana/dashboards/24965-litellm/)
- [Redis Configuration](https://redis.io/docs/manual/config/)

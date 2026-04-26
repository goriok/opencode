# 0005 — Prometheus Exporter for Token Metrics

- **Status**: Proposed
- **Data**: 2026-04-26

## Contexto

We have token dashboard (HTML self-contained) but need Grafana/Prometheus integration for real-time monitoring and alerting. The supervisor wants to monitor token usage per source (opencode vs claude_code) with historical trending.

## Decisão

Build a Prometheus exporter (token_tracker/exporter.py) serving /metrics with:
- opencode_tokens_total{source, model, agent} — token consumption
- opencode_cost_tracked_total{source, model, agent} — tracked cost
- opencode_cost_estimated_total{source, model, agent} — estimated API cost
- opencode_messages_total{source, agent} — message count

Lightweight HTTP server using prometheus_client library. Reuses existing token_tracker adapters (opencode.py, claude_code.py) — zero code changes to them.

## Alternativas Consideradas

1. **Timeseries DB (InfluxDB/TimescaleDB)** — Too heavy for local use, requires separate DB server
2. **Direct SQLite queries from Grafana** — Fragile, no label support, breaks on schema changes
3. **JSON API + Grafana JSON datasource** — Requires Grafana plugin, not standard Prometheus
4. **Prometheus Exporter** ✅ — Standard, any Grafana can consume it, labels provide flexibility

## Consequências

**Positivas:**
- Standard Prometheus metrics — any Grafana instance can consume
- Zero DB changes needed — reuses existing adapters
- Labels (source/model/agent) enable flexible querying
- No infrastructure changes — just another Python script

**Negativas:**
- New Python dependency: prometheus_client
- HTTP server to manage (small footprint)
- Requires Prometheus + Grafana running (already available)

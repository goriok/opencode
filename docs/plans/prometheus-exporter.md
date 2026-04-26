# Prometheus Exporter for Token Metrics

**Status**: Plan

## Goal

Add a Prometheus exporter HTTP endpoint to the token-tracker Python package, serving four token-usage metrics (`opencode_tokens_total`, `opencode_cost_tracked_total`, `opencode_cost_estimated_total`, `opencode_messages_total`) with `{source, model}` labels, plus a `servemetrics` CLI subcommand and supporting documentation.

## Context

This plan implements the decision recorded in [MADR 0005](../madr/0005-prometheus-exporter-token-metrics.md) (Proposed). The existing token-tracker generates an HTML dashboard but lacks a Prometheus scrape endpoint for Grafana integration. The solution uses the `prometheus_client` Python library on port 9090, reuses existing adapters, and requires a `source` data field to label metrics by origin (opencode vs claude_code).

## Affected Files

### Phase 1 — Source field propagation

| Action | File | Reason |
|--------|------|--------|
| modify | `token_tracker/models.py` | Add `source` field to aggregate models (`DailyAggregate`, `AgentAggregate`, `ModelAggregate`, `KPIs`) so Prometheus labels can distinguish opencode vs claude_code data |
| modify | `token_tracker/adapters/__init__.py` | Expose module-level constants (`SOURCE_OPENCODE`, `SOURCE_CLAUDE_CODE`) for consistent source tagging |
| modify | `token_tracker/adapters/opencode.py` | Set `source="opencode"` on all records returned by fetch methods |
| modify | `token_tracker/adapters/claude_code.py` | Set `source="claude_code"` on all records returned by fetch methods |
| modify | `token_tracker/cli.py` | Update merge helpers (`_merge_daily`, `_merge_agents`, `_merge_models`) to carry `source` through merged aggregates; update `_print_dry_run` to show source breakdown |
| modify | `tests/test_opencode_adapter.py` | Assert `source` field on adapter output |
| modify | `tests/test_claude_code_adapter.py` | Assert `source` field on adapter output |
| modify | `tests/test_models.py` | Test `source` default and assignment |

### Phase 2 — Exporter module

| Action | File | Reason |
|--------|------|--------|
| create | `token_tracker/exporter.py` | New module: Prometheus HTTP server, 4 metric definitions, data collection loop, `/metrics` endpoint on port 9090 |
| modify | `pyproject.toml` | Add `prometheus-client` to project dependencies |
| create | `tests/test_exporter.py` | Unit tests: metric registration, data collection, HTTP handler |

### Phase 3 — CLI integration and documentation

| Action | File | Reason |
|--------|------|--------|
| modify | `token_tracker/cli.py` | Add `servemetrics` subcommand via argparse (port, host, days flags); wire to `exporter.py` entry point |
| modify | `token_tracker/__main__.py` | Route `servemetrics` to the new CLI subcommand |
| modify | `docs/handbooks/token-tracker.md` | Add "Prometheus Exporter" section — usage, metric reference, example scrape config |
| create | `docs/runbooks/rb-007-prometheus-exporter.md` | New runbook: "Iniciar e configurar o Prometheus exporter" |
| modify | `docs/runbooks/README.md` | Add RB-007 to runbook index |

## Implementation Steps

### Phase 1: Source field (models + adapters)

```
1. In token_tracker/adapters/__init__.py:
   - Add SOURCE_OPENCODE = "opencode" and SOURCE_CLAUDE_CODE = "claude_code" constants

2. In token_tracker/models.py:
   - Add source: str = "" field to DailyAggregate, AgentAggregate, KPIs
   - (MessageRecord already has source)
   - Keep source as a simple string — Prometheus uses it directly as a label value

3. In token_tracker/adapters/opencode.py:
   - OpenCodeAdapter constructor: accept an optional source param (default SOURCE_OPENCODE)
   - In fetch_daily / fetch_agents / fetch_models: set source = self.source on each result
   - No DB schema changes needed — source is a data-layer annotation, not a DB column

4. In token_tracker/adapters/claude_code.py:
   - ClaudeCodeAdapter constructor: accept an optional source param (default SOURCE_CLAUDE_CODE)
   - In fetch_daily / fetch_agents / fetch_models: set source = self.source on each result

5. In token_tracker/cli.py:
   - Update _merge_daily, _merge_agents, _merge_models to preserve source per-merge-group
     or drop source at merge boundary (since Prometheus exporter will query raw, not merged)
   - Keep source out of merge logic — the merged aggregates lose source granularity,
     but the CLI doesn't need it; the exporter will query adapters directly

6. In tests:
   - test_opencode_adapter: verify source == "opencode" on adapter output
   - test_claude_code_adapter: verify source == "claude_code" on adapter output
   - test_models: verify DailyAggregate(source="test") round-trips
```

### Phase 2: Exporter module

```
1. In pyproject.toml:
   - Add "prometheus-client>=0.19,<1.0" to dependencies

2. Create token_tracker/exporter.py:
   - HTTP server using prometheus_client.start_http_server(port=9090)
   - Define 4 Gauge/Counter metrics:
     a. opencode_tokens_total{source, model}
        — sum of total_tokens per source+model
     b. opencode_cost_tracked_total{source, model}
        — sum of tracked_cost per source+model
     c. opencode_cost_estimated_total{source, model}
        — sum of est_api_cost per source+model
     d. opencode_messages_total{source}
        — message count per source

   - Data collection flow:
     a. Instantiate OpenCodeAdapter and ClaudeCodeAdapter
     b. Call fetch_models() on each (which returns ModelAggregate with source)
     c. For each ModelAggregate: set gauge label values {source, model}
     d. Call fetch_daily() on each for message counts → opencode_messages_total

   - export_metrics(port=9090, host="0.0.0.0", days=30) entry point:
     - Sets up metrics
     - Starts HTTP server
     - Runs collection once (metrics persist until process dies)
     - Logs startup message

3. Create tests/test_exporter.py:
   - Test metric registration: all 4 metrics exist after setup
   - Test data collection: mocked adapter returns known records, verify gauge values
   - Test HTTP handler: start_http_server responds on /metrics
```

### Phase 3: CLI + docs

```
1. In token_tracker/cli.py:
   - Add "servemetrics" subcommand to build_parser():
     --port (default 9090)
     --host (default "0.0.0.0")
     --days (default 30)
   - In main(): if args.command == "servemetrics", call exporter.export_metrics(...)
   - Keep existing argparse structure — add subparser group for commands

2. In token_tracker/__main__.py:
   - Ensure the servemetrics subcommand is routed to cli.main()

3. In docs/handbooks/token-tracker.md:
   - Add "Prometheus Exporter" section after existing content:
     - Quick start: `uv run token-tracker servemetrics`
     - Metric reference table
     - Example prometheus.yml scrape_config
     - Grafana dashboard hint (import by ID)

4. Create docs/runbooks/rb-007-prometheus-exporter.md:
   - Title: "RB-007 — Iniciar e configurar o Prometheus exporter"
   - Steps: install, configure prometheus.yml, start exporter, verify /metrics
   - Validation: curl localhost:9090/metrics shows 4 opencode_* metrics
   - Troubleshooting: port conflict, missing data, adapter errors

5. Edit docs/runbooks/README.md:
   - Add RB-007 row to index table
```

## Open Questions

1. **Polling vs pushing** — The current plan uses a one-shot collect + serve model (metrics set once at startup). Should `exporter.py` implement a periodic refresh (e.g., every 60s via `time.sleep` loop or `apscheduler`) to pick up new data without restarting the process? MADR 0005 is silent on this.
2. **Port conflict** — Port 9090 is the Prometheus default; if Grafana/Prometheus is already running locally, we may need a configurable default. The `--port` flag covers this, but should we document a non-standard default (e.g., 9099) to avoid collisions?
3. **Source encoding** — The `source` field on aggregate models may not survive merge operations in `cli.py`. The exporter bypasses merges by querying adapters directly, so this is fine for the exporter but the field addition is still useful for future direct adapter queries.

## Status

- [ ] Phase 1: Source field in models and adapters
- [ ] Phase 2: Exporter module (token_tracker/exporter.py)
- [ ] Phase 3: CLI subcommand and documentation

## TODOs

- [ ] Add `SOURCE_OPENCODE` / `SOURCE_CLAUDE_CODE` constants to `token_tracker/adapters/__init__.py`
- [ ] Add `source` field to `DailyAggregate`, `AgentAggregate`, `KPIs` models
- [ ] Tag adapter fetch methods with `source` per adapter type
- [ ] Update adapter tests to assert `source` field
- [ ] Add `prometheus-client` to `pyproject.toml`
- [ ] Create `token_tracker/exporter.py` — 4 metrics + HTTP server on port 9090
- [ ] Create `tests/test_exporter.py` — metric registration and HTTP tests
- [ ] Add `servemetrics` subcommand to `token_tracker/cli.py`
- [ ] Wire `servemetrics` in `token_tracker/__main__.py`
- [ ] Update `docs/handbooks/token-tracker.md` with exporter section
- [ ] Create `docs/runbooks/rb-007-prometheus-exporter.md`
- [ ] Update `docs/runbooks/README.md` index with RB-007

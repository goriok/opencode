---
date: 2026-04-26
topic: "Token Tracking Timeline"
status: validated
---

# Token Tracking Timeline — Design Document

## Problem Statement

Need a **baseline of token usage per session over time** to compare whether new AI strategies are more effective. OpenCode already records all token/cost/agent/model data in SQLite (`~/.local/share/opencode/opencode.db`), but there's no way to visualize trends, compare sessions, or track efficiency improvements over time.

Current data volume: 2,539 assistant messages, ~147M tokens, $1.48 tracked cost across 94 sessions.

## Constraints

- **Zero external dependencies** — must work with just `sqlite3` and standard Unix tools
- **No server required** — dashboard must be open-and-see, no Grafana/Jupyter/etc
- **Data source is read-only** — we read from OpenCode's existing SQLite, never modify it
- **Must work offline** — CDN for Chart.js is the only network dependency (can be vendored later)
- **Must handle subagent hierarchy** — sessions spawned by subagents have `parent_id` linking to parent

## Approach

**Bash script → HTML dashboard with Chart.js**. The script queries the existing SQLite database, computes aggregations and derived metrics, then generates a self-contained HTML file with inline data as JSON and Chart.js from CDN.

Alternatives considered and rejected:
- **Grafana + Prometheus**: Overkill, requires running server
- **Jupyter Notebook**: Requires Python + libs, too heavy for this
- **Pure CLI text output**: Works but impossible to see visual trends

## Architecture

```
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│   opencode.db    │──────▶│  token-tracker    │──────▶│   dashboard.html  │
│  (SQLite exist.) │  SQL  │  (Bash script)   │ query │  (self-contained) │
└──────────────────┘       └──────────────────┘       └──────────────────┘
                                    │
                                    ▼
                           ┌──────────────────┐
                           │  baseline JSON    │
                           │  (snapshot files) │
                           └──────────────────┘
```

## Components

### 1. `token-tracker.sh` — Main Script

**Location**: `~/.config/opencode/token-tracker.sh`

**Responsibilities**:
- Connect to SQLite at `~/.local/share/opencode/opencode.db`
- Generate aggregations by day, session, agent, model
- Calculate derived metrics (tokens/output, cache hit rate, cost per session)
- Load previous baseline snapshot if exists, compute deltas
- Emit self-contained HTML with Chart.js + inline JSON data
- Save baseline snapshot to `~/.config/opencode/token-baselines/`

**CLI flags**:
- `--output <path>` — output HTML path (default: `~/.config/opencode/token-dashboard.html`)
- `--days <N>` — look back N days (default: 30)
- `--dry-run` — print stats to terminal, no HTML generation
- `--baseline <label>` — save baseline snapshot with this label
- `--compare <label>` — compare against a specific baseline
- `--validate` — validate existing baseline files

### 2. Dashboard Views

| View | Description | Metrics |
|------|-------------|---------|
| **Daily Timeline** | Day-by-day line chart | total tokens, input, output, cache hit rate, cost |
| **Per Session** | Interactive table with sort | tokens total, cost, duration, agents used |
| **Per Agent** | Efficiency by agent | avg tokens/msg, output ratio, cache hit |
| **Per Model** | Model comparison | tokens, cost, usage distribution |
| **Efficiency** | Quality metrics over time | tokens/output, cache effectiveness, cost efficiency |

### 3. Key Metrics (KPIs)

**Primary (baseline)**:
- **Tokens per day** — total volume by type (input/output/cache)
- **Cost per day** — spend in USD
- **Sessions per day** — activity level
- **Messages per session** — engagement depth

**Derived (efficiency)**:
- **Cache Hit Rate**: `cache.read / tokens.total` — how much context is served from cache vs re-processed
- **Output Ratio**: `tokens.output / tokens.total` — how much spend becomes useful output vs context overhead
- **Cost per Output Token**: `cost / tokens.output` — real cost efficiency
- **Tokens per Session**: `tokens.total / sessions` — average session "weight"

**Comparative (strategy evaluation)**:
- **Before/After delta** — percent change vs baseline period
- **Agent Efficiency** — which agent delivers most output per token
- **Model ROI** — which model has best cost/benefit ratio

### 4. Baseline Snapshot System

**Location**: `~/.config/opencode/token-baselines/`

**File format**: `baseline-<label>.json`
```json
{
  "label": "pre-strategy-change",
  "created_at": "2026-04-26T02:30:00Z",
  "period": { "from": "2026-03-26", "to": "2026-04-26" },
  "metrics": {
    "total_tokens": 147000000,
    "total_cost": 1.48,
    "total_sessions": 94,
    "avg_tokens_per_session": 1564000,
    "cache_hit_rate": 0.85,
    "output_ratio": 0.07,
    "cost_per_output_token": 0.0000015,
    "daily_avg_tokens": 5000000,
    "daily_avg_cost": 0.05
  },
  "by_agent": { ... },
  "by_model": { ... },
  "by_day": [ ... ]
}
```

When comparing, the dashboard shows **delta columns** (e.g. "+12% tokens, -5% cost, +8% cache hit rate").

### 5. Dashboard HTML Structure

Self-contained HTML with:
- Chart.js from CDN (can be vendored for offline)
- All data embedded as JSON in a `<script>` tag
- Responsive layout with Tailwind CSS (CDN)
- Dark mode support (matches OpenCode aesthetic)

**Sections**:
1. **Header** — generation date, period covered, totals
2. **KPI Cards** — 4-6 key metrics with trend arrows (↑↓ vs baseline)
3. **Daily Timeline Chart** — multi-series line chart (input, output, cache tokens)
4. **Cost Chart** — bar chart with daily cost
5. **Session Table** — sortable table (tokens, cost, date, agent)
6. **Agent Breakdown** — pie chart + efficiency table
7. **Model Comparison** — horizontal bar chart
8. **Efficiency Metrics** — line chart for cache hit rate and output ratio over time

## Data Flow

```
1. User runs: bash token-tracker.sh
2. Script connects to SQLite
3. Queries:
   a. Aggregated by day (tokens, cost, cache)
   b. Aggregated by session (with parent_id for subagent grouping)
   c. Aggregated by agent
   d. Aggregated by model
4. Script calculates derived metrics
5. Script loads previous baseline (if exists)
6. Script calculates deltas vs baseline
7. Script generates HTML with Chart.js + inline data
8. Script saves baseline snapshot as JSON
9. Script opens browser (or prints path)
```

## Data Model — Key SQL Queries

The script uses these core queries against the existing `message` table:

**Daily aggregation**:
```sql
SELECT date(time_created/1000, 'unixepoch') as day,
       COUNT(*) as msgs,
       SUM(json_extract(data, '$.tokens.total')) as total_tokens,
       SUM(json_extract(data, '$.tokens.input')) as input_tokens,
       SUM(json_extract(data, '$.tokens.output')) as output_tokens,
       SUM(json_extract(data, '$.tokens.cache.read')) as cache_read,
       SUM(json_extract(data, '$.tokens.cache.write')) as cache_write,
       SUM(json_extract(data, '$.cost')) as total_cost
FROM message
WHERE json_extract(data, '$.role') = 'assistant'
GROUP BY day ORDER BY day
```

**Session aggregation** (with subagent rollup):
```sql
-- Sessions with their direct tokens
SELECT s.id, s.slug, s.title, s.parent_id,
       datetime(s.time_created/1000, 'unixepoch') as created,
       COUNT(m.id) as msgs,
       SUM(json_extract(m.data, '$.cost')) as total_cost,
       SUM(json_extract(m.data, '$.tokens.total')) as total_tokens,
       SUM(json_extract(m.data, '$.tokens.input')) as input_tokens,
       SUM(json_extract(m.data, '$.tokens.output')) as output_tokens
FROM session s
JOIN message m ON m.session_id = s.id
WHERE json_extract(m.data, '$.role') = 'assistant'
GROUP BY s.id
ORDER BY s.time_created DESC
```

**Subagent rollup**: Sessions with `parent_id IS NOT NULL` get their tokens added to the parent session for "total effort per conversation" metrics.

## Error Handling

- **SQLite not found** → clear message with install instructions
- **Empty database** → empty dashboard with "No sessions found" message
- **Browser not available** → just print file path
- **Corrupted baseline** → skip comparison, generate without delta, show warning
- **Permission denied on DB** → suggest running with appropriate permissions or copying DB

## Testing Strategy

- **Dry-run mode** (`--dry-run`): run queries, print stats to terminal, no HTML generation
- **Snapshot validation** (`--validate`): verify baseline JSON is valid and comparable
- **Manual verification**: compare dashboard totals with OpenCode's native UI display
- **Idempotency**: running the script multiple times produces identical output (baseline snapshots are additive, never overwritten)

## Open Questions

1. **Baseline period**: What's the ideal period for the first snapshot? Defaulting to 30 days, adjustable via `--days`.
2. **Granularity**: Is daily sufficient or do we need hourly breakdowns for active sessions?
3. **Subagent rollup**: Should subagent tokens always be summed into parent session, or shown both ways?
4. **Offline Chart.js**: Should we vendor Chart.js for fully offline operation, or is CDN acceptable?
5. **Auto-refresh**: Should the script support a `--watch` mode that regenerates periodically?
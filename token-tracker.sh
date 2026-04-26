#!/usr/bin/env bash
#
# token-tracker.sh — OpenCode token usage timeline dashboard
#
# Usage:
#   bash ~/.config/opencode/token-tracker.sh [options]
#
# What it does:
#   1. Reads token/cost/agent/model data from OpenCode's SQLite database
#   2. Generates a self-contained HTML dashboard with Chart.js
#   3. Saves baseline snapshots for before/after comparison
#
# Options:
#   --output <path>      Output HTML path (default: ~/.config/opencode/token-dashboard.html)
#   --days <N>           Look back N days (default: 30)
#   --dry-run            Print stats to terminal, no HTML generation
#   --baseline <label>   Save baseline snapshot with this label
#   --compare <label>    Compare against a specific baseline
#   --validate           Validate existing baseline files
#   --open               Open dashboard in browser after generation

set -euo pipefail

# ── Colors ──────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { printf "${GREEN}[token-tracker]${NC} %s\n" "$*"; }
warn()  { printf "${YELLOW}[token-tracker]${NC} %s\n" "$*"; }
error() { printf "${RED}[token-tracker]${NC} %s\n" "$*" >&2; exit 1; }

# ── Defaults ─────────────────────────────────────────────────────────────────
DB_PATH="${HOME}/.local/share/opencode/opencode.db"
OUTPUT_PATH="${HOME}/.config/opencode/token-dashboard.html"
BASELINE_DIR="${HOME}/.config/opencode/token-baselines"
DAYS=30
DRY_RUN=false
OPEN_BROWSER=false
BASELINE_LABEL=""
COMPARE_LABEL=""
VALIDATE=false

# ── Parse Args ──────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --output)   OUTPUT_PATH="$2"; shift 2 ;;
    --days)     DAYS="$2"; shift 2 ;;
    --dry-run)  DRY_RUN=true; shift ;;
    --baseline) BASELINE_LABEL="$2"; shift 2 ;;
    --compare)  COMPARE_LABEL="$2"; shift 2 ;;
    --validate) VALIDATE=true; shift ;;
    --open)     OPEN_BROWSER=true; shift ;;
    -h|--help)
      head -15 "$0" | grep '^#' | sed 's/^# \?//'
      exit 0
      ;;
    *) warn "Unknown option: $1"; shift ;;
  esac
done

# ── Validate ─────────────────────────────────────────────────────────────────
if [[ ! -f "$DB_PATH" ]]; then
  error "OpenCode database not found at $DB_PATH. Is OpenCode installed?"
fi

if ! command -v sqlite3 &>/dev/null; then
  error "sqlite3 not found. Install it: brew install sqlite3 (macOS) or apt install sqlite3 (Linux)"
fi

mkdir -p "$BASELINE_DIR"

# ── SQL Queries ──────────────────────────────────────────────────────────────

# Filter: only assistant messages with actual token data, within date range
DATE_FILTER="json_extract(m.data, '$.role') = 'assistant' AND json_extract(m.data, '$.tokens.total') IS NOT NULL AND m.time_created >= strftime('%s', 'now', '-${DAYS} days') * 1000"

SQL_DAILY="
SELECT date(m.time_created/1000, 'unixepoch') as day,
       COUNT(*) as msgs,
       SUM(json_extract(m.data, '$.tokens.total')) as total_tokens,
       SUM(json_extract(m.data, '$.tokens.input')) as input_tokens,
       SUM(json_extract(m.data, '$.tokens.output')) as output_tokens,
       SUM(json_extract(m.data, '$.tokens.reasoning')) as reasoning_tokens,
       COALESCE(SUM(json_extract(m.data, '$.tokens.cache.read')), 0) as cache_read,
       COALESCE(SUM(json_extract(m.data, '$.tokens.cache.write')), 0) as cache_write,
       SUM(json_extract(m.data, '$.cost')) as total_cost
FROM message m
WHERE ${DATE_FILTER}
GROUP BY day ORDER BY day"

SQL_SESSIONS="
SELECT s.id, s.slug, s.title, s.parent_id,
       datetime(s.time_created/1000, 'unixepoch') as created,
       COUNT(m.id) as msgs,
       COALESCE(SUM(json_extract(m.data, '$.tokens.total')), 0) as total_tokens,
       COALESCE(SUM(json_extract(m.data, '$.tokens.input')), 0) as input_tokens,
       COALESCE(SUM(json_extract(m.data, '$.tokens.output')), 0) as output_tokens,
       COALESCE(SUM(json_extract(m.data, '$.cost')), 0) as total_cost,
       COALESCE(SUM(json_extract(m.data, '$.tokens.cache.read')), 0) as cache_read
FROM session s
LEFT JOIN message m ON m.session_id = s.id AND json_extract(m.data, '$.role') = 'assistant' AND json_extract(m.data, '$.tokens.total') IS NOT NULL
WHERE s.time_created >= strftime('%s', 'now', '-${DAYS} days') * 1000
GROUP BY s.id
ORDER BY s.time_created DESC"

SQL_AGENTS="
SELECT json_extract(m.data, '$.agent') as agent,
       COUNT(*) as msgs,
       SUM(json_extract(m.data, '$.tokens.total')) as total_tokens,
       SUM(json_extract(m.data, '$.tokens.input')) as input_tokens,
       SUM(json_extract(m.data, '$.tokens.output')) as output_tokens,
       COALESCE(SUM(json_extract(m.data, '$.tokens.cache.read')), 0) as cache_read,
       SUM(json_extract(m.data, '$.cost')) as total_cost
FROM message m
WHERE ${DATE_FILTER}
GROUP BY agent ORDER BY total_tokens DESC"

SQL_MODELS="
SELECT json_extract(m.data, '$.modelID') as model,
       json_extract(m.data, '$.providerID') as provider,
       COUNT(*) as msgs,
       SUM(json_extract(m.data, '$.tokens.total')) as total_tokens,
       SUM(json_extract(m.data, '$.tokens.input')) as input_tokens,
       SUM(json_extract(m.data, '$.tokens.output')) as output_tokens,
       COALESCE(SUM(json_extract(m.data, '$.tokens.cache.read')), 0) as cache_read,
       SUM(json_extract(m.data, '$.cost')) as tracked_cost
FROM message m
WHERE ${DATE_FILTER}
GROUP BY model ORDER BY total_tokens DESC"

# ── Query Helper ─────────────────────────────────────────────────────────────
run_query() {
  local query="$1"
  sqlite3 -json "$DB_PATH" "$query" 2>/dev/null || echo "[]"
}

# ── Fetch Data ──────────────────────────────────────────────────────────────
info "Fetching data from OpenCode database (last ${DAYS} days)..."

DAILY_DATA=$(run_query "$SQL_DAILY")
SESSION_DATA=$(run_query "$SQL_SESSIONS")
AGENT_DATA=$(run_query "$SQL_AGENTS")
MODEL_DATA=$(run_query "$SQL_MODELS")

# ── Estimated API Cost ──────────────────────────────────────────────────────
# The "cost" field in OpenCode's DB is what providers report, which is misleading:
# - opencode-go models: report per-token cost, but subscription is flat $5-10/mo
# - anthropic/github-copilot/opencode: report cost=0, but you pay subscription
# We calculate what these tokens WOULD cost at published API rates.
PRICING_TABLE=$(python3 -c "
import json
pricing = {
    'claude-sonnet-4-6':  (3.00/1e6, 15.00/1e6, 0.30/1e6),
    'claude-sonnet-4.6':  (3.00/1e6, 15.00/1e6, 0.30/1e6),
    'claude-opus-4-6':    (15.00/1e6, 75.00/1e6, 1.50/1e6),
    'claude-opus-4.6':    (15.00/1e6, 75.00/1e6, 1.50/1e6),
    'claude-haiku-4-5':   (0.80/1e6, 4.00/1e6, 0.08/1e6),
    'glm-5.1':            (0, 0, 0),
    'deepseek-v4-flash':  (0, 0, 0),
    'deepseek-v4-pro':    (0, 0, 0),
    'minimax-m2.7':       (0, 0, 0),
    'big-pickle':         (0, 0, 0),
}
print(json.dumps(pricing))
" 2>/dev/null || echo '{}')

EST_API_COST=$(echo "$MODEL_DATA" | python3 -c "
import json, sys
pricing = json.loads('''${PRICING_TABLE}''')
data = json.load(sys.stdin)
total = 0
for m in data:
    p = pricing.get(m.get('model',''), (0,0,0))
    total += m.get('input_tokens',0) * p[0]
    total += m.get('output_tokens',0) * p[1]
    total += m.get('cache_read',0) * p[2]
print(round(total, 2))
" 2>/dev/null || echo "0")

# Inject per-model est_api_cost into MODEL_DATA
MODEL_DATA=$(echo "$MODEL_DATA" | python3 -c "
import json, sys
pricing = json.loads('''${PRICING_TABLE}''')
data = json.load(sys.stdin)
for m in data:
    p = pricing.get(m.get('model',''), (0,0,0))
    m['est_api_cost'] = round(
        m.get('input_tokens',0) * p[0] +
        m.get('output_tokens',0) * p[1] +
        m.get('cache_read',0) * p[2], 4)
print(json.dumps(data))
" 2>/dev/null || echo '[]')

# ── Compute Summary Stats ───────────────────────────────────────────────────
SUMMARY=$(echo "$DAILY_DATA" | python3 -c "
import json, sys
data = json.load(sys.stdin)
if not data:
    print(json.dumps({'total_tokens': 0, 'tracked_cost': 0, 'est_api_cost': 0, 'total_msgs': 0, 'days': 0, 'avg_tokens_day': 0, 'avg_tracked_cost_day': 0, 'avg_est_cost_day': 0, 'cache_hit_rate': 0, 'output_ratio': 0, 'tracked_cost_per_output': 0, 'est_cost_per_output': 0}))
    sys.exit(0)
total_tokens = sum(r.get('total_tokens', 0) or 0 for r in data)
tracked_cost = sum(r.get('total_cost', 0) or 0 for r in data)
total_msgs = sum(r.get('msgs', 0) for r in data)
total_input = sum(r.get('input_tokens', 0) or 0 for r in data)
total_output = sum(r.get('output_tokens', 0) or 0 for r in data)
total_cache_read = sum(r.get('cache_read', 0) or 0 for r in data)
days = len(data)
cache_hit_rate = (total_cache_read / total_tokens * 100) if total_tokens > 0 else 0
output_ratio = (total_output / total_tokens * 100) if total_tokens > 0 else 0
tracked_per_output = (tracked_cost / total_output) if total_output > 0 else 0
print(json.dumps({
    'total_tokens': total_tokens,
    'total_output': total_output,
    'tracked_cost': round(tracked_cost, 4),
    'est_api_cost': 0,
    'total_msgs': total_msgs,
    'days': days,
    'avg_tokens_day': round(total_tokens / days) if days > 0 else 0,
    'avg_tracked_cost_day': round(tracked_cost / days, 4) if days > 0 else 0,
    'avg_est_cost_day': 0,
    'cache_hit_rate': round(cache_hit_rate, 1),
    'output_ratio': round(output_ratio, 1),
    'tracked_cost_per_output': round(tracked_per_output, 8),
    'est_cost_per_output': 0
}))
" 2>/dev/null)

SUMMARY=$(python3 -c "
import json
s = json.loads('''${SUMMARY}''')
s['est_api_cost'] = float('''${EST_API_COST}''' or '0')
s['avg_est_cost_day'] = round(s['est_api_cost'] / s['days'], 2) if s['days'] > 0 else 0
s['est_cost_per_output'] = round(s['est_api_cost'] / s['total_output'], 8) if s.get('total_output', 0) > 0 else 0
print(json.dumps(s))
" 2>/dev/null)

# ── Baseline Handling ────────────────────────────────────────────────────────
BASELINE_DELTA="null"

if [[ -n "$COMPARE_LABEL" ]]; then
  BASELINE_FILE="${BASELINE_DIR}/baseline-${COMPARE_LABEL}.json"
  if [[ -f "$BASELINE_FILE" ]]; then
    info "Loading baseline '${COMPARE_LABEL}' for comparison..."
    BASELINE_DELTA=$(python3 -c "
import json, sys
current = json.loads('''${SUMMARY}''')
with open('${BASELINE_FILE}') as f:
    prev = json.load(f)['metrics']
def pct(curr, prev_val):
    if prev_val == 0: return 'N/A'
    return f'{((curr - prev_val) / prev_val * 100):+.1f}%'
print(json.dumps({
    'total_tokens': pct(current['total_tokens'], prev['total_tokens']),
    'tracked_cost': pct(current['tracked_cost'], prev.get('tracked_cost', current['tracked_cost'])),
    'est_api_cost': pct(current['est_api_cost'], prev.get('est_api_cost', 0) or current['est_api_cost']),
    'cache_hit_rate': pct(current['cache_hit_rate'], prev['cache_hit_rate']),
    'output_ratio': pct(current['output_ratio'], prev['output_ratio']),
    'avg_tokens_day': pct(current['avg_tokens_day'], prev['avg_tokens_day']),
    'avg_tracked_cost_day': pct(current['avg_tracked_cost_day'], prev.get('avg_tracked_cost_day', current['avg_tracked_cost_day'])),
    'avg_est_cost_day': pct(current['avg_est_cost_day'], prev.get('avg_est_cost_day', current['avg_est_cost_day']))
}))
" 2>/dev/null)
  else
    warn "Baseline '${COMPARE_LABEL}' not found at ${BASELINE_FILE}"
  fi
fi

# ── Save Baseline ───────────────────────────────────────────────────────────
if [[ -n "$BASELINE_LABEL" ]]; then
  BASELINE_FILE="${BASELINE_DIR}/baseline-${BASELINE_LABEL}.json"
  info "Saving baseline snapshot as '${BASELINE_LABEL}'..."
  python3 -c "
import json
from datetime import datetime, timezone
summary = json.loads('''${SUMMARY}''')
baseline = {
    'label': '${BASELINE_LABEL}',
    'created_at': datetime.now(timezone.utc).isoformat(),
    'period_days': ${DAYS},
    'metrics': summary,
    'daily': json.loads('''${DAILY_DATA}'''),
    'agents': json.loads('''${AGENT_DATA}'''),
    'models': json.loads('''${MODEL_DATA}''')
}
with open('${BASELINE_FILE}', 'w') as f:
    json.dump(baseline, f, indent=2)
print(f'Baseline saved to ${BASELINE_FILE}')
" 2>/dev/null
fi

# ── Validate Baselines ──────────────────────────────────────────────────────
if [[ "$VALIDATE" == true ]]; then
  info "Validating baseline files in ${BASELINE_DIR}..."
  for f in "${BASELINE_DIR}"/baseline-*.json; do
    [[ -f "$f" ]] || continue
    if python3 -c "import json; json.load(open('$f'))" 2>/dev/null; then
      printf "  ${GREEN}✓${NC} %s\n" "$(basename "$f")"
    else
      printf "  ${RED}✗${NC} %s (invalid JSON)\n" "$(basename "$f")"
    fi
  done
  exit 0
fi

# ── Dry Run ─────────────────────────────────────────────────────────────────
if [[ "$DRY_RUN" == true ]]; then
  printf "\n${CYAN}═══ Token Tracker — Dry Run ═══${NC}\n\n"
  echo "$SUMMARY" | python3 -c "
import json, sys
s = json.load(sys.stdin)
print(f'  Period:            Last ${DAYS} days')
print(f'  Total Tokens:      {s[\"total_tokens\"]:>,}')
print(f'  Tracked Cost:     \${s[\"tracked_cost\"]}')
print(f'  Est. API Cost:     \${s[\"est_api_cost\"]}')
print(f'  Messages:          {s[\"total_msgs\"]:>,}')
print(f'  Active Days:       {s[\"days\"]}')
print(f'  Avg Tokens/Day:    {s[\"avg_tokens_day\"]:>,}')
print(f'  Avg Tracked/Day:   \${s[\"avg_tracked_cost_day\"]}')
print(f'  Avg Est.API/Day:   \${s[\"avg_est_cost_day\"]}')
print(f'  Cache Hit Rate:    {s[\"cache_hit_rate\"]}%')
print(f'  Output Ratio:      {s[\"output_ratio\"]}%')
print(f'  Tracked/Output Tk: \${s[\"tracked_cost_per_output\"]:.6f}')
print(f'  Est.API/Output Tk: \${s[\"est_cost_per_output\"]:.6f}')
" 2>/dev/null
  printf "\n${CYAN}── Agents ──${NC}\n"
  echo "$AGENT_DATA" | python3 -c "
import json, sys
for a in json.load(sys.stdin):
    print(f'  {a[\"agent\"]:30s}  {a[\"total_tokens\"]:>12,} tkns  {a[\"msgs\"]:>5} msgs  \${a[\"total_cost\"]:.4f}')
" 2>/dev/null
  printf "\n${CYAN}── Models ──${NC}\n"
  echo "$MODEL_DATA" | python3 -c "
import json, sys
for m in json.load(sys.stdin):
    est = m.get('est_api_cost', 0)
    tc = m.get('tracked_cost', 0)
    print(f'  {m[\"model\"]:30s}  {m[\"total_tokens\"]:>12,} tkns  {m[\"msgs\"]:>5} msgs  \${tc:.4f} tracked  \${est:.4f} est.api')
" 2>/dev/null
  exit 0
fi

# ── Generate HTML Dashboard ─────────────────────────────────────────────────
info "Generating dashboard HTML..."

FORMAT_DAILY=$(echo "$DAILY_DATA" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(json.dumps(data))
" 2>/dev/null)

FORMAT_SESSIONS=$(echo "$SESSION_DATA" | python3 -c "
import json, sys
data = json.load(sys.stdin)
# Truncate title for display
for s in data:
    s['title'] = (s['title'] or 'Untitled')[:60]
    s['slug'] = s['slug'] or s['id'][:8]
print(json.dumps(data))
" 2>/dev/null)

FORMAT_AGENTS=$(echo "$AGENT_DATA" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(json.dumps(data))
" 2>/dev/null)

FORMAT_MODELS=$(echo "$MODEL_DATA" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(json.dumps(data))
" 2>/dev/null)

cat > "$OUTPUT_PATH" << 'HEREDOC_START'
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OpenCode Token Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
  :root {
    --bg-primary: #0d1117;
    --bg-secondary: #161b22;
    --bg-card: #1c2128;
    --border: #30363d;
    --text-primary: #e6edf3;
    --text-secondary: #8b949e;
    --accent-blue: #58a6ff;
    --accent-green: #3fb950;
    --accent-orange: #d29922;
    --accent-red: #f85149;
    --accent-purple: #bc8cff;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    padding: 24px;
    max-width: 1400px;
    margin: 0 auto;
  }
  h1 { font-size: 1.5rem; margin-bottom: 8px; }
  h2 { font-size: 1.1rem; color: var(--text-secondary); margin-bottom: 16px; }
  .subtitle { color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 24px; }
  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 12px;
    margin-bottom: 24px;
  }
  .kpi-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px;
  }
  .kpi-label { font-size: 0.75rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; }
  .kpi-value { font-size: 1.5rem; font-weight: 700; margin: 4px 0; }
  .kpi-delta { font-size: 0.8rem; }
  .kpi-delta.up { color: var(--accent-red); }
  .kpi-delta.down { color: var(--accent-green); }
  .kpi-delta.neutral { color: var(--text-secondary); }
  .chart-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-bottom: 24px;
  }
  .chart-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px;
  }
  .chart-card.full-width {
    grid-column: 1 / -1;
  }
  .chart-title {
    font-size: 0.9rem;
    font-weight: 600;
    margin-bottom: 12px;
    color: var(--text-primary);
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
  }
  th {
    text-align: left;
    padding: 8px 12px;
    background: var(--bg-secondary);
    color: var(--text-secondary);
    font-weight: 600;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    cursor: pointer;
    user-select: none;
    border-bottom: 1px solid var(--border);
  }
  th:hover { color: var(--accent-blue); }
  td {
    padding: 8px 12px;
    border-bottom: 1px solid var(--border);
    color: var(--text-primary);
  }
  tr:hover td { background: var(--bg-secondary); }
  .num { text-align: right; font-variant-numeric: tabular-nums; }
  .badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.7rem;
    font-weight: 600;
  }
  .badge-agent { background: #1f3a5f; color: var(--accent-blue); }
  .badge-model { background: #2d1f4e; color: var(--accent-purple); }
  @media (max-width: 768px) {
    .chart-grid { grid-template-columns: 1fr; }
    body { padding: 12px; }
  }
</style>
</head>
<body>

<h1>⚡ OpenCode Token Dashboard</h1>
<p class="subtitle" id="subtitle"></p>
<p id="cost-warning" style="background:rgba(210,153,34,0.15);border:1px solid #d29922;border-radius:6px;padding:8px 12px;margin-bottom:16px;font-size:0.8rem;color:#d29922;">
⚠️ <strong>Tracked Cost</strong> = what providers report (opencode-go only, $0 for Anthropic/Copilot). <strong>Est. API Cost</strong> = what these tokens would cost at published API rates. Your real cost is the flat subscription.
</p>

<!-- KPI Cards -->
<div class="kpi-grid" id="kpi-grid"></div>

<!-- Timeline Charts -->
<div class="chart-grid">
  <div class="chart-card full-width">
    <div class="chart-title">Daily Token Usage</div>
    <canvas id="tokensChart"></canvas>
  </div>
  <div class="chart-card">
    <div class="chart-title">Daily Tracked Cost</div>
    <canvas id="costChart"></canvas>
  </div>
  <div class="chart-card">
    <div class="chart-title">Cache Hit Rate Over Time</div>
    <canvas id="cacheChart"></canvas>
  </div>
</div>

<!-- Agent & Model Breakdown -->
<div class="chart-grid">
  <div class="chart-card">
    <div class="chart-title">Tokens by Agent</div>
    <canvas id="agentChart"></canvas>
  </div>
  <div class="chart-card">
    <div class="chart-title">Tokens by Model</div>
    <canvas id="modelChart"></canvas>
  </div>
</div>

<!-- Agent Efficiency Table -->
<div class="chart-card" style="margin-bottom:24px">
  <div class="chart-title">Agent Efficiency</div>
  <table id="agentTable">
    <thead><tr>
      <th onclick="sortTable('agentTable',0)">Agent</th>
      <th class="num" onclick="sortTable('agentTable',1)">Messages</th>
      <th class="num" onclick="sortTable('agentTable',2)">Total Tokens</th>
      <th class="num" onclick="sortTable('agentTable',3)">Output Tokens</th>
      <th class="num" onclick="sortTable('agentTable',4)">Output Ratio</th>
      <th class="num" onclick="sortTable('agentTable',5)">Cache Hit</th>
      <th class="num" onclick="sortTable('agentTable',6)">Tracked $</th>
    </tr></thead>
    <tbody></tbody>
  </table>
</div>

<!-- Model Comparison Table -->
<div class="chart-card" style="margin-bottom:24px">
  <div class="chart-title">Model Comparison</div>
  <table id="modelTable">
    <thead><tr>
      <th onclick="sortTable('modelTable',0)">Model</th>
      <th class="num" onclick="sortTable('modelTable',1)">Messages</th>
      <th class="num" onclick="sortTable('modelTable',2)">Total Tokens</th>
      <th class="num" onclick="sortTable('modelTable',3)">Output Tokens</th>
      <th class="num" onclick="sortTable('modelTable',4)">Cache Hit</th>
      <th class="num" onclick="sortTable('modelTable',5)">Tracked $</th>
      <th class="num" onclick="sortTable('modelTable',6)">Est.API $</th>
      <th class="num" onclick="sortTable('modelTable',7)">$/1K Out</th>
    </tr></thead>
    <tbody></tbody>
  </table>
</div>

<!-- Session Table -->
<div class="chart-card" style="margin-bottom:24px">
  <div class="chart-title">Recent Sessions</div>
  <table id="sessionTable">
    <thead><tr>
      <th onclick="sortTable('sessionTable',0)">Session</th>
      <th onclick="sortTable('sessionTable',1)">Created</th>
      <th class="num" onclick="sortTable('sessionTable',2)">Messages</th>
      <th class="num" onclick="sortTable('sessionTable',3)">Total Tokens</th>
      <th class="num" onclick="sortTable('sessionTable',4)">Output Tokens</th>
      <th class="num" onclick="sortTable('sessionTable',5)">Cache Hit</th>
      <th class="num" onclick="sortTable('sessionTable',6)">Tracked $</th>
    </tr></thead>
    <tbody></tbody>
  </table>
</div>

<footer style="text-align:center;color:var(--text-secondary);font-size:0.75rem;padding:24px 0">
  Generated by <strong>token-tracker.sh</strong> — OpenCode Token Dashboard
</footer>

<script>
// ── Data ──────────────────────────────────────────────────────────────────
const SUMMARY = SUMMARY_DATA;
const DAILY = DAILY_DATA;
const SESSIONS = SESSION_DATA;
const AGENTS = AGENT_DATA;
const MODELS = MODEL_DATA;
const DELTA = DELTA_DATA;

// ── Helpers ────────────────────────────────────────────────────────────────
const fmt = (n) => {
  if (n === null || n === undefined) return '—';
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K';
  return n.toLocaleString();
};
const fmt$ = (n) => n < 0.01 ? '$' + n.toFixed(4) : '$' + n.toFixed(2);
const pct = (n) => (n === null || n === undefined) ? '—' : n.toFixed(1) + '%';

// ── KPI Cards ──────────────────────────────────────────────────────────────
const kpis = [
  { label: 'Total Tokens', value: fmt(SUMMARY.total_tokens), delta: DELTA?.total_tokens },
  { label: 'Tracked Cost', value: fmt$(SUMMARY.tracked_cost), delta: DELTA?.tracked_cost },
  { label: 'Est. API Cost', value: fmt$(SUMMARY.est_api_cost), delta: DELTA?.est_api_cost },
  { label: 'Messages', value: SUMMARY.total_msgs.toLocaleString(), delta: null },
  { label: 'Active Days', value: SUMMARY.days, delta: null },
  { label: 'Cache Hit Rate', value: pct(SUMMARY.cache_hit_rate), delta: DELTA?.cache_hit_rate },
  { label: 'Output Ratio', value: pct(SUMMARY.output_ratio), delta: DELTA?.output_ratio },
  { label: 'Avg Tokens/Day', value: fmt(SUMMARY.avg_tokens_day), delta: DELTA?.avg_tokens_day },
  { label: 'Avg Tracked/Day', value: fmt$(SUMMARY.avg_tracked_cost_day), delta: DELTA?.avg_tracked_cost_day },
  { label: 'Avg Est.API/Day', value: fmt$(SUMMARY.avg_est_cost_day), delta: DELTA?.avg_est_cost_day },
];

document.getElementById('subtitle').textContent =
  `Last ${SUMMARY.days} days · ${new Date().toLocaleDateString()}`;

const kpiGrid = document.getElementById('kpi-grid');
kpis.forEach(k => {
  const deltaHtml = k.delta
    ? `<div class="kpi-delta ${k.delta.startsWith('-') ? 'down' : 'up'}">${k.delta}</div>`
    : '';
  kpiGrid.innerHTML += `
    <div class="kpi-card">
      <div class="kpi-label">${k.label}</div>
      <div class="kpi-value">${k.value}</div>
      ${deltaHtml}
    </div>`;
});

// ── Chart Config ───────────────────────────────────────────────────────────
Chart.defaults.color = '#8b949e';
Chart.defaults.borderColor = '#30363d';
Chart.defaults.font.family = "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";

const dailyLabels = DAILY.map(d => d.day);

// ── Tokens Timeline ─────────────────────────────────────────────────────────
new Chart(document.getElementById('tokensChart'), {
  type: 'line',
  data: {
    labels: dailyLabels,
    datasets: [
      { label: 'Total', data: DAILY.map(d => d.total_tokens), borderColor: '#58a6ff', backgroundColor: 'rgba(88,166,255,0.1)', fill: true, tension: 0.3 },
      { label: 'Input', data: DAILY.map(d => d.input_tokens), borderColor: '#d29922', backgroundColor: 'transparent', tension: 0.3 },
      { label: 'Output', data: DAILY.map(d => d.output_tokens), borderColor: '#3fb950', backgroundColor: 'transparent', tension: 0.3 },
      { label: 'Cache Read', data: DAILY.map(d => d.cache_read), borderColor: '#bc8cff', backgroundColor: 'transparent', borderDash: [5,5], tension: 0.3 },
    ]
  },
  options: {
    responsive: true,
    interaction: { mode: 'index', intersect: false },
    plugins: { legend: { position: 'top' } },
    scales: {
      y: { ticks: { callback: v => fmt(v) } }
    }
  }
});

// ── Cost Chart ──────────────────────────────────────────────────────────────
new Chart(document.getElementById('costChart'), {
  type: 'bar',
  data: {
    labels: dailyLabels,
    datasets: [{
      label: 'Daily Cost ($)',
      data: DAILY.map(d => d.total_cost),
      backgroundColor: 'rgba(88,166,255,0.7)',
      borderColor: '#58a6ff',
      borderWidth: 1,
    }]
  },
  options: {
    responsive: true,
    plugins: { legend: { display: false } },
    scales: {
      y: { ticks: { callback: v => '$' + v.toFixed(2) } }
    }
  }
});

// ── Cache Hit Rate ─────────────────────────────────────────────────────────
new Chart(document.getElementById('cacheChart'), {
  type: 'line',
  data: {
    labels: dailyLabels,
    datasets: [{
      label: 'Cache Hit Rate (%)',
      data: DAILY.map(d => d.total_tokens > 0 ? (d.cache_read / d.total_tokens * 100) : 0),
      borderColor: '#bc8cff',
      backgroundColor: 'rgba(188,140,255,0.1)',
      fill: true,
      tension: 0.3,
    }]
  },
  options: {
    responsive: true,
    scales: {
      y: { min: 0, max: 100, ticks: { callback: v => v + '%' } }
    }
  }
});

// ── Agent Pie Chart ─────────────────────────────────────────────────────────
const agentColors = ['#58a6ff','#3fb950','#d29922','#f85149','#bc8cff','#79c0ff','#56d4dd','#e3b341','#ff7b72','#a5d6ff'];
new Chart(document.getElementById('agentChart'), {
  type: 'doughnut',
  data: {
    labels: AGENTS.slice(0, 10).map(a => a.agent),
    datasets: [{
      data: AGENTS.slice(0, 10).map(a => a.total_tokens),
      backgroundColor: agentColors,
    }]
  },
  options: {
    responsive: true,
    plugins: { legend: { position: 'right', labels: { boxWidth: 12 } } }
  }
});

// ── Model Bar Chart ────────────────────────────────────────────────────────
new Chart(document.getElementById('modelChart'), {
  type: 'bar',
  data: {
    labels: MODELS.map(m => m.model),
    datasets: [{
      label: 'Total Tokens',
      data: MODELS.map(m => m.total_tokens),
      backgroundColor: 'rgba(188,140,255,0.7)',
      borderColor: '#bc8cff',
    }]
  },
  options: {
    responsive: true,
    indexAxis: 'y',
    plugins: { legend: { display: false } },
    scales: {
      x: { ticks: { callback: v => fmt(v) } }
    }
  }
});

// ── Agent Table ─────────────────────────────────────────────────────────────
const agentTbody = document.querySelector('#agentTable tbody');
AGENTS.forEach(a => {
  const outputRatio = a.total_tokens > 0 ? (a.output_tokens / a.total_tokens * 100).toFixed(1) : '0';
  const cacheHit = a.total_tokens > 0 ? (a.cache_read / a.total_tokens * 100).toFixed(1) : '0';
  agentTbody.innerHTML += `<tr>
    <td><span class="badge badge-agent">${a.agent}</span></td>
    <td class="num">${a.msgs.toLocaleString()}</td>
    <td class="num">${fmt(a.total_tokens)}</td>
    <td class="num">${fmt(a.output_tokens)}</td>
    <td class="num">${outputRatio}%</td>
    <td class="num">${cacheHit}%</td>
    <td class="num">${fmt$(a.total_cost)}</td>
  </tr>`;
});

// ── Model Table ────────────────────────────────────────────────────────────
const modelTbody = document.querySelector('#modelTable tbody');
MODELS.forEach(m => {
  const cacheHit = m.total_tokens > 0 ? (m.cache_read / m.total_tokens * 100).toFixed(1) : '0';
  const trackedPerK = m.output_tokens > 0 ? (m.tracked_cost / m.output_tokens * 1000).toFixed(4) : '0';
  const estApiPerK = m.output_tokens > 0 ? (m.est_api_cost / m.output_tokens * 1000).toFixed(4) : '0';
  modelTbody.innerHTML += `<tr>
    <td><span class="badge badge-model">${m.model}</span></td>
    <td class="num">${m.msgs.toLocaleString()}</td>
    <td class="num">${fmt(m.total_tokens)}</td>
    <td class="num">${fmt(m.output_tokens)}</td>
    <td class="num">${cacheHit}%</td>
    <td class="num">${fmt$(m.tracked_cost)}</td>
    <td class="num">${fmt$(m.est_api_cost)}</td>
    <td class="num">${estApiPerK}</td>
  </tr>`;
});

// ── Session Table ──────────────────────────────────────────────────────────
const sessionTbody = document.querySelector('#sessionTable tbody');
SESSIONS.forEach(s => {
  const cacheHit = s.total_tokens > 0 ? (s.cache_read / s.total_tokens * 100).toFixed(1) : '0';
  sessionTbody.innerHTML += `<tr>
    <td>${s.slug || s.id.slice(0,8)} <span style="color:var(--text-secondary);font-size:0.8em">${s.title}</span></td>
    <td>${s.created ? s.created.slice(0,16) : '—'}</td>
    <td class="num">${s.msgs}</td>
    <td class="num">${fmt(s.total_tokens)}</td>
    <td class="num">${fmt(s.output_tokens)}</td>
    <td class="num">${cacheHit}%</td>
    <td class="num">${fmt$(s.total_cost)}</td>
  </tr>`;
});

// ── Sort Helper ─────────────────────────────────────────────────────────────
function sortTable(tableId, colIdx) {
  const table = document.getElementById(tableId);
  const tbody = table.querySelector('tbody');
  const rows = Array.from(tbody.querySelectorAll('tr'));
  const ths = table.querySelectorAll('th');
  const isAsc = ths[colIdx].dataset.sort !== 'asc';
  ths.forEach(t => delete t.dataset.sort);
  ths[colIdx].dataset.sort = isAsc ? 'asc' : 'desc';
  rows.sort((a, b) => {
    let aVal = a.cells[colIdx].textContent.trim();
    let bVal = b.cells[colIdx].textContent.trim();
    // Numeric sort for num cells
    aVal = aVal.replace(/[$,%KMB]/g, '');
    bVal = bVal.replace(/[$,%KMB]/g, '');
    const aNum = parseFloat(aVal);
    const bNum = parseFloat(bVal);
    if (!isNaN(aNum) && !isNaN(bNum)) {
      return isAsc ? aNum - bNum : bNum - aNum;
    }
    return isAsc ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
  });
  rows.forEach(r => tbody.appendChild(r));
}
</script>
</body>
</html>
HEREDOC_START

# ── Inject Data ─────────────────────────────────────────────────────────────
python3 << PYEOF
import re

with open("${OUTPUT_PATH}", "r") as f:
    html = f.read()

html = html.replace("SUMMARY_DATA", '''${SUMMARY}''', 1)
html = html.replace("DAILY_DATA", '''${FORMAT_DAILY}''', 1)
html = html.replace("SESSION_DATA", '''${FORMAT_SESSIONS}''', 1)
html = html.replace("AGENT_DATA", '''${FORMAT_AGENTS}''', 1)
html = html.replace("MODEL_DATA", '''${FORMAT_MODELS}''', 1)
html = html.replace("DELTA_DATA", '''${BASELINE_DELTA}''', 1)

with open("${OUTPUT_PATH}", "w") as f:
    f.write(html)
PYEOF

info "Dashboard generated at ${OUTPUT_PATH}"

# ── Open Browser ────────────────────────────────────────────────────────────
if [[ "$OPEN_BROWSER" == true ]]; then
  if [[ "$(uname)" == "Darwin" ]]; then
    open "$OUTPUT_PATH"
  elif command -v xdg-open &>/dev/null; then
    xdg-open "$OUTPUT_PATH"
  else
    info "Open manually: ${OUTPUT_PATH}"
  fi
fi

info "Done!"
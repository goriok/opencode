"""HTML dashboard generator with Chart.js."""

from __future__ import annotations

import json
import webbrowser
from dataclasses import asdict
from typing import Dict, List, Optional

from token_tracker.models import (
    AgentAggregate,
    DailyAggregate,
    KPIs,
    ModelAggregate,
    SessionSummary,
)


def compute_kpis(
    daily: List[DailyAggregate],
    agents: List[AgentAggregate],
    models: List[ModelAggregate],
    days: int = 30,
) -> KPIs:
    """Compute summary KPIs from raw aggregated data."""
    total_tokens = sum(d.total_tokens for d in daily)
    total_msgs = sum(d.msgs for d in daily)
    total_input = sum(d.input_tokens for d in daily)
    total_output = sum(d.output_tokens for d in daily)
    total_cache_read = sum(d.cache_read for d in daily)
    tracked_cost = sum(d.total_cost for d in daily)
    active_days = len(daily) if daily else 0

    est_api_cost = sum(m.est_api_cost for m in models)

    cache_hit_rate = (total_cache_read / total_tokens * 100) if total_tokens > 0 else 0
    output_ratio = (total_output / total_tokens * 100) if total_tokens > 0 else 0
    tokens_per_day = round(total_tokens / active_days) if active_days > 0 else 0
    avg_tracked_cost_day = round(tracked_cost / active_days, 4) if active_days > 0 else 0
    avg_est_cost_day = round(est_api_cost / active_days, 4) if active_days > 0 else 0
    cost_per_output = round(tracked_cost / total_output, 8) if total_output > 0 else 0

    return KPIs(
        total_tokens=total_tokens,
        total_cost=round(tracked_cost, 4),
        total_msgs=total_msgs,
        active_days=active_days,
        cache_hit_rate=round(cache_hit_rate, 1),
        output_ratio=round(output_ratio, 1),
        cost_per_output_token=cost_per_output,
        tokens_per_day=tokens_per_day,
        avg_tracked_cost_day=avg_tracked_cost_day,
        avg_est_cost_day=avg_est_cost_day,
    )


def generate_dashboard(
    daily: List[DailyAggregate],
    sessions: List[SessionSummary],
    agents: List[AgentAggregate],
    models: List[ModelAggregate],
    kpis: KPIs,
    delta: Optional[Dict[str, str]] = None,
    source: str = "opencode",
    days: int = 30,
) -> str:
    """Generate self-contained HTML dashboard with Chart.js."""
    summary_data = json.dumps({
        "total_tokens": kpis.total_tokens,
        "tracked_cost": kpis.total_cost,
        "est_api_cost": kpis.avg_est_cost_day * kpis.active_days if kpis.active_days else 0,
        "total_msgs": kpis.total_msgs,
        "total_output": sum(d.output_tokens for d in daily),
        "days": kpis.active_days,
        "avg_tokens_day": kpis.tokens_per_day,
        "avg_tracked_cost_day": kpis.avg_tracked_cost_day,
        "avg_est_cost_day": kpis.avg_est_cost_day,
        "cache_hit_rate": kpis.cache_hit_rate,
        "output_ratio": kpis.output_ratio,
    })

    daily_data = json.dumps([asdict(d) for d in daily])
    session_data = json.dumps([{
        "id": s.session_id,
        "slug": s.slug,
        "title": (s.title or "Untitled")[:60],
        "created": s.created,
        "msgs": s.msgs,
        "total_tokens": s.total_tokens,
        "output_tokens": s.output_tokens,
        "cache_read": s.cache_read,
        "total_cost": s.cost,
    } for s in sessions])
    agent_data = json.dumps([asdict(a) for a in agents])
    model_data = json.dumps([asdict(m) for m in models])
    delta_data = json.dumps(delta) if delta else "null"

    html = _TEMPLATE.replace("SUMMARY_DATA", summary_data, 1)
    html = html.replace("DAILY_DATA", daily_data, 1)
    html = html.replace("SESSION_DATA", session_data, 1)
    html = html.replace("AGENT_DATA", agent_data, 1)
    html = html.replace("MODEL_DATA", model_data, 1)
    html = html.replace("DELTA_DATA", delta_data, 1)
    html = html.replace("SOURCE_LABEL", source, 1)

    return html


def write_dashboard(html: str, output_path: str) -> str:
    """Write dashboard HTML to file and return the path."""
    path = _ensure_parent(output_path)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return str(path)


def open_dashboard(path: str) -> None:
    """Open the dashboard file in the default browser."""
    abs_path = _ensure_parent(path)
    webbrowser.open(f"file://{abs_path}")


def _ensure_parent(path: str) -> str:
    """Ensure parent directory exists and return absolute path."""
    from pathlib import Path
    p = Path(path).expanduser().resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    return str(p)


# ── HTML Template ────────────────────────────────────────────────────────────

_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Token Dashboard — SOURCE_LABEL</title>
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

<h1>&#9889; Token Dashboard</h1>
<p class="subtitle" id="subtitle"></p>
<p id="cost-warning" style="background:rgba(210,153,34,0.15);border:1px solid #d29922;border-radius:6px;padding:8px 12px;margin-bottom:16px;font-size:0.8rem;color:#d29922;">
&#9888;&#65039; <strong>Tracked Cost</strong> = what providers report (opencode-go only, $0 for Anthropic/Copilot). <strong>Est. API Cost</strong> = what these tokens would cost at published API rates. Your real cost is the flat subscription.
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
  Generated by <strong>token-tracker</strong> &mdash; Token Dashboard
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
  if (n === null || n === undefined) return '\u2014';
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K';
  return n.toLocaleString();
};
const fmt$ = (n) => n < 0.01 ? '$' + n.toFixed(4) : '$' + n.toFixed(2);
const pct = (n) => (n === null || n === undefined) ? '\u2014' : n.toFixed(1) + '%';

// ── KPI Cards ──────────────────────────────────────────────────────────────
const kpis = [
  { label: 'Total Tokens', value: fmt(SUMMARY.total_tokens), delta: DELTA?.total_tokens },
  { label: 'Tracked Cost', value: fmt$(SUMMARY.tracked_cost), delta: DELTA?.tracked_cost },
  { label: 'Est. API Cost', value: fmt$(SUMMARY.est_api_cost || 0), delta: DELTA?.est_api_cost },
  { label: 'Messages', value: SUMMARY.total_msgs.toLocaleString(), delta: null },
  { label: 'Active Days', value: SUMMARY.days, delta: null },
  { label: 'Cache Hit Rate', value: pct(SUMMARY.cache_hit_rate), delta: DELTA?.cache_hit_rate },
  { label: 'Output Ratio', value: pct(SUMMARY.output_ratio), delta: DELTA?.output_ratio },
  { label: 'Avg Tokens/Day', value: fmt(SUMMARY.avg_tokens_day), delta: DELTA?.avg_tokens_day },
  { label: 'Avg Tracked/Day', value: fmt$(SUMMARY.avg_tracked_cost_day || 0), delta: DELTA?.avg_tracked_cost_day },
  { label: 'Avg Est.API/Day', value: fmt$(SUMMARY.avg_est_cost_day || 0), delta: DELTA?.avg_est_cost_day },
];

document.getElementById('subtitle').textContent =
  `Last ${SUMMARY.days} days \u00b7 ${new Date().toLocaleDateString()}`;

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
    <td>${s.created ? s.created.slice(0,16) : '\u2014'}</td>
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
</html>"""
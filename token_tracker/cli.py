"""CLI argument parser and main entry point for token-tracker."""

from __future__ import annotations

import argparse
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional

from token_tracker.adapters.claude_code import ClaudeCodeAdapter, DEFAULT_CLAUDE_DIR
from token_tracker.adapters.opencode import OpenCodeAdapter, DEFAULT_DB_PATH
from token_tracker.baselines import (
    DEFAULT_BASELINE_DIR,
    compare_baselines,
    load_baseline,
    save_baseline,
    validate_baselines,
)
from token_tracker.dashboard import compute_kpis, generate_dashboard, open_dashboard, write_dashboard
from token_tracker.models import (
    AgentAggregate,
    DailyAggregate,
    KPIs,
    ModelAggregate,
    SessionSummary,
    SubagentInfo,
)

DEFAULT_OUTPUT_PATH = Path.home() / ".config" / "opencode" / "token-dashboard.html"
DEFAULT_DAYS = 30


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for token-tracker."""
    parser = argparse.ArgumentParser(
        prog="token-tracker",
        description="Unified token usage tracker for OpenCode and Claude Code",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    serve_parser = subparsers.add_parser("servemetrics", help="Start Prometheus metrics HTTP server")
    serve_parser.add_argument("--port", type=int, default=9090, help="HTTP port (default: 9090)")
    serve_parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
    serve_parser.add_argument("--days", type=int, default=30, help="Lookback days (default: 30)")
    parser.add_argument(
        "--source",
        choices=["opencode", "claude-code", "auto"],
        default="auto",
        help="Data source (default: auto-detect)",
    )
    parser.add_argument(
        "--db",
        type=str,
        default=None,
        help=f"OpenCode SQLite DB path (default: {DEFAULT_DB_PATH})",
    )
    parser.add_argument(
        "--claude-dir",
        type=str,
        default=None,
        help="Claude Code projects directory (default: ~/.claude/projects/)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help=f"Output HTML path (default: {DEFAULT_OUTPUT_PATH})",
    )
    parser.add_argument(
        "--days",
        "-d",
        type=int,
        default=DEFAULT_DAYS,
        help=f"Number of days to look back (default: {DEFAULT_DAYS})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print stats to terminal without generating HTML",
    )
    parser.add_argument(
        "--baseline",
        type=str,
        default=None,
        metavar="LABEL",
        help="Save current metrics as a named baseline",
    )
    parser.add_argument(
        "--compare",
        type=str,
        default=None,
        metavar="LABEL",
        help="Compare current metrics against a saved baseline",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate all baseline files for data integrity",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open output in browser after generation",
    )
    parser.add_argument(
        "--with-subagents",
        action="store_true",
        help="Include Claude Code subagent tracking data",
    )
    parser.add_argument(
        "--baseline-dir",
        type=str,
        default=None,
        help=f"Baseline storage directory (default: {DEFAULT_BASELINE_DIR})",
    )
    return parser


def _detect_sources(args: argparse.Namespace) -> List[str]:
    """Auto-detect available data sources based on path existence."""
    if args.source != "auto":
        return [args.source]

    sources: List[str] = []
    db_path = Path(args.db) if args.db else DEFAULT_DB_PATH
    if db_path.exists():
        sources.append("opencode")

    claude_dir = Path(args.claude_dir) if args.claude_dir else DEFAULT_CLAUDE_DIR
    projects_dir = claude_dir / "projects"
    if projects_dir.is_dir():
        sources.append("claude-code")

    return sources


def _merge_daily(*lists: List[DailyAggregate]) -> List[DailyAggregate]:
    """Merge multiple daily aggregate lists, summing by day."""
    merged: Dict[str, DailyAggregate] = {}
    for daily_list in lists:
        for d in daily_list:
            if d.day not in merged:
                merged[d.day] = DailyAggregate(day=d.day, source=d.source)
            m = merged[d.day]
            m.msgs += d.msgs
            m.total_tokens += d.total_tokens
            m.input_tokens += d.input_tokens
            m.output_tokens += d.output_tokens
            m.reasoning_tokens += d.reasoning_tokens
            m.cache_read += d.cache_read
            m.cache_write += d.cache_write
            m.total_cost += d.total_cost
    return sorted(merged.values(), key=lambda d: d.day)


def _merge_agents(*lists: List[AgentAggregate]) -> List[AgentAggregate]:
    """Merge multiple agent aggregate lists, summing by agent name."""
    merged: Dict[str, AgentAggregate] = {}
    for agent_list in lists:
        for a in agent_list:
            if a.agent not in merged:
                merged[a.agent] = AgentAggregate(agent=a.agent, source=a.source)
            m = merged[a.agent]
            m.msgs += a.msgs
            m.total_tokens += a.total_tokens
            m.input_tokens += a.input_tokens
            m.output_tokens += a.output_tokens
            m.cache_read += a.cache_read
            m.total_cost += a.total_cost
    return sorted(merged.values(), key=lambda a: a.total_tokens, reverse=True)


def _merge_models(*lists: List[ModelAggregate]) -> List[ModelAggregate]:
    """Merge multiple model aggregate lists, summing by model name."""
    merged: Dict[str, ModelAggregate] = {}
    for model_list in lists:
        for m in model_list:
            if m.model not in merged:
                merged[m.model] = ModelAggregate(model=m.model, provider=m.provider, source=m.source)
            e = merged[m.model]
            e.msgs += m.msgs
            e.total_tokens += m.total_tokens
            e.input_tokens += m.input_tokens
            e.output_tokens += m.output_tokens
            e.cache_read += m.cache_read
            e.tracked_cost += m.tracked_cost
            e.est_api_cost += m.est_api_cost
    return sorted(merged.values(), key=lambda m: m.total_tokens, reverse=True)


def _merge_sessions(*lists: List[SessionSummary]) -> List[SessionSummary]:
    """Merge session lists — concatenate, dedup by session_id."""
    seen: Dict[str, SessionSummary] = {}
    for session_list in lists:
        for s in session_list:
            if s.session_id not in seen:
                seen[s.session_id] = s
            else:
                existing = seen[s.session_id]
                existing.msgs += s.msgs
                existing.total_tokens += s.total_tokens
                existing.input_tokens += s.input_tokens
                existing.output_tokens += s.output_tokens
                existing.cost += s.cost
                existing.cache_read += s.cache_read
    return sorted(seen.values(), key=lambda s: s.created, reverse=True)


def _fmt_num(n: int | float) -> str:
    """Format large numbers with K/M suffixes."""
    if isinstance(n, float):
        if n < 0.01:
            return f"${n:.4f}"
        return f"${n:.2f}"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def _fmt_pct(n: float) -> str:
    """Format a percentage with 1 decimal."""
    return f"{n:.1f}%"


def _print_dry_run(
    source_label: str,
    days: int,
    daily: List[DailyAggregate],
    sessions: List[SessionSummary],
    agents: List[AgentAggregate],
    models: List[ModelAggregate],
    kpis: KPIs,
    delta: Optional[Dict] = None,
    subagents: Optional[List[SubagentInfo]] = None,
) -> None:
    """Print formatted stats to terminal (dry-run mode)."""
    print(f"\n{'='*60}")
    print(f" Token Tracker — {source_label} — Last {days} days")
    print(f"{'='*60}\n")

    print("  KPI Summary")
    print(f"    Total Tokens:     {_fmt_num(kpis.total_tokens)}")
    print(f"    Tracked Cost:     {_fmt_num(kpis.total_cost)}")
    print(f"    Est. API Cost:    {_fmt_num(kpis.avg_est_cost_day * kpis.active_days if kpis.active_days else 0)}")
    print(f"    Messages:         {kpis.total_msgs:,}")
    print(f"    Active Days:      {kpis.active_days}")
    print(f"    Cache Hit Rate:   {_fmt_pct(kpis.cache_hit_rate)}")
    print(f"    Output Ratio:     {_fmt_pct(kpis.output_ratio)}")
    print(f"    Tokens/Day:       {_fmt_num(kpis.tokens_per_day)}")
    print(f"    Avg Tracked/Day:  {_fmt_num(kpis.avg_tracked_cost_day)}")
    print(f"    Avg Est.API/Day:  {_fmt_num(kpis.avg_est_cost_day)}")

    if delta:
        print(f"\n  Baseline Comparison: {delta.get('previous_label', '?')} → now")
        metrics_map = {
            "total_tokens": "Total Tokens",
            "total_cost": "Tracked Cost",
            "cache_hit_rate": "Cache Hit Rate",
            "output_ratio": "Output Ratio",
            "tokens_per_day": "Tokens/Day",
        }
        for key, label in metrics_map.items():
            d = delta.get(key, "N/A")
            print(f"    {label}: {d}")

    if agents:
        print(f"\n  Top Agents (by tokens)")
        for a in agents[:10]:
            ratio = (a.output_tokens / a.total_tokens * 100) if a.total_tokens > 0 else 0
            print(f"    {a.agent:<20} {a.total_tokens:>10} tokens  {a.msgs:>5} msgs  {ratio:.1f}% out")

    if models:
        print(f"\n  Top Models (by tokens)")
        for m in models[:10]:
            print(f"    {m.model:<30} {m.total_tokens:>10} tokens  {m.msgs:>5} msgs  ${m.tracked_cost:.2f} tracked  ${m.est_api_cost:.2f} est")

    print(f"\n  Sessions: {len(sessions)} total")
    if sessions:
        top_sessions = sorted(sessions, key=lambda s: s.total_tokens, reverse=True)[:5]
        for s in top_sessions:
            name = s.slug or s.title or s.session_id[:8]
            print(f"    {name:<30} {s.total_tokens:>10} tokens  {s.msgs:>4} msgs")

    if subagents:
        print(f"\n  Subagents ({len(subagents)} found)")
        for sa in sorted(subagents, key=lambda s: s.tokens.total, reverse=True)[:10]:
            print(f"    {sa.agent_type:<25} {sa.tokens.total:>10} tokens  model={sa.model}")

    print()


def main(argv: list[str] | None = None) -> None:
    """Main entry point: parse args, fetch data, generate output."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if getattr(args, "command", None) == "servemetrics":
        from token_tracker.exporter import export_metrics

        port = getattr(args, "port", 9090)
        host = getattr(args, "host", "0.0.0.0")
        days = getattr(args, "days", 30)
        export_metrics(port=port, host=host, days=days)
        return

    db_path = Path(args.db) if args.db else DEFAULT_DB_PATH
    claude_dir = Path(args.claude_dir) if args.claude_dir else DEFAULT_CLAUDE_DIR
    output_path = Path(args.output) if args.output else DEFAULT_OUTPUT_PATH
    baseline_dir = Path(args.baseline_dir) if args.baseline_dir else DEFAULT_BASELINE_DIR
    days = args.days

    if args.validate:
        issues = validate_baselines(baseline_dir)
        if issues:
            print("Baseline validation issues found:")
            for issue in issues:
                print(f"  ✗ {issue}")
            sys.exit(1)
        else:
            print("All baselines are valid.")
            return

    sources = _detect_sources(args)
    if not sources:
        print("No data sources found.", file=sys.stderr)
        print("  — Run with --source opencode if you have an OpenCode database", file=sys.stderr)
        print("  — Run with --source claude-code if you have Claude Code session files", file=sys.stderr)
        print(f"  — Checked: {db_path} and {claude_dir / 'projects'}", file=sys.stderr)
        sys.exit(1)

    source_label = " + ".join(sources)

    all_daily: List[DailyAggregate] = []
    all_sessions: List[SessionSummary] = []
    all_agents: List[AgentAggregate] = []
    all_models: List[ModelAggregate] = []

    for source in sources:
        if source == "opencode":
            if not db_path.exists():
                print(f"OpenCode database not found at {db_path}", file=sys.stderr)
                continue
            adapter = OpenCodeAdapter(db_path=db_path)
            try:
                all_daily.append(adapter.fetch_daily(days))
                all_sessions.append(adapter.fetch_sessions(days))
                all_agents.append(adapter.fetch_agents(days))
                all_models.append(adapter.fetch_models(days))
            except Exception as e:
                print(f"Error reading OpenCode database: {e}", file=sys.stderr)
                continue

        elif source == "claude-code":
            projects_dir = claude_dir / "projects"
            if not projects_dir.is_dir():
                print(f"Claude Code projects directory not found: {projects_dir}", file=sys.stderr)
                continue
            adapter = ClaudeCodeAdapter(claude_dir=claude_dir)
            try:
                all_daily.append(adapter.fetch_daily(days))
                all_sessions.append(adapter.fetch_sessions(days))
                all_agents.append(adapter.fetch_agents(days))
                all_models.append(adapter.fetch_models(days))
            except Exception as e:
                print(f"Error reading Claude Code data: {e}", file=sys.stderr)
                continue

    daily = _merge_daily(*all_daily) if all_daily else []
    sessions = _merge_sessions(*all_sessions) if all_sessions else []
    agents = _merge_agents(*all_agents) if all_agents else []
    models = _merge_models(*all_models) if all_models else []

    if not daily and not sessions:
        print(f"No data found for {source_label} source in the last {days} days.")
        sys.exit(0)

    kpis = compute_kpis(daily, agents, models, days)
    delta = None

    subagents: List[SubagentInfo] = []
    if args.with_subagents and "claude-code" in sources:
        claude_adapter = ClaudeCodeAdapter(claude_dir=claude_dir)
        try:
            subagents = claude_adapter.fetch_subagents(days)
        except Exception as e:
            print(f"Error reading subagent data: {e}", file=sys.stderr)

    if args.compare:
        try:
            previous = load_baseline(args.compare, baseline_dir)
        except FileNotFoundError:
            print(f"Baseline '{args.compare}' not found in {baseline_dir}", file=sys.stderr)
            sys.exit(1)

        current_metrics = {
            "total_tokens": kpis.total_tokens,
            "total_cost": kpis.total_cost,
            "total_msgs": kpis.total_msgs,
            "input_tokens": sum(d.input_tokens for d in daily),
            "output_tokens": sum(d.output_tokens for d in daily),
            "cache_read": sum(d.cache_read for d in daily),
            "reasoning_tokens": sum(d.reasoning_tokens for d in daily),
            "cache_hit_rate": kpis.cache_hit_rate,
            "output_ratio": kpis.output_ratio,
            "cost_per_output_token": kpis.cost_per_output_token,
            "tokens_per_day": kpis.tokens_per_day,
            "period_days": days,
        }

        current_baseline = {
            "label": "current",
            "metrics": current_metrics,
            "daily": [asdict(d) for d in daily],
            "agents": [asdict(a) for a in agents],
            "models": [asdict(m) for m in models],
        }
        delta = compare_baselines(current_baseline, previous)

    if args.baseline:
        current_metrics = {
            "total_tokens": kpis.total_tokens,
            "total_cost": kpis.total_cost,
            "total_msgs": kpis.total_msgs,
            "input_tokens": sum(d.input_tokens for d in daily),
            "output_tokens": sum(d.output_tokens for d in daily),
            "cache_read": sum(d.cache_read for d in daily),
            "reasoning_tokens": sum(d.reasoning_tokens for d in daily),
            "cache_hit_rate": kpis.cache_hit_rate,
            "output_ratio": kpis.output_ratio,
            "cost_per_output_token": kpis.cost_per_output_token,
            "tokens_per_day": kpis.tokens_per_day,
            "period_days": days,
        }

        baseline_path = save_baseline(
            label=args.baseline,
            metrics=current_metrics,
            daily=[asdict(d) for d in daily],
            agents=[asdict(a) for a in agents],
            models=[asdict(m) for m in models],
            output_dir=baseline_dir,
        )
        print(f"Baseline '{args.baseline}' saved to {baseline_path}")

    if args.dry_run:
        _print_dry_run(source_label, days, daily, sessions, agents, models, kpis, delta, subagents=subagents)
        if args.open:
            print("Note: --open is ignored with --dry-run")
        return

    html = generate_dashboard(daily, sessions, agents, models, kpis, delta, source_label, days)
    path = write_dashboard(html, str(output_path))
    print(f"Dashboard written to {path}")

    if args.open:
        open_dashboard(path)


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Session Usage Analyzer Workflow

Analyzes token consumption in opencode sessions using the opencode CLI export.
"""

import argparse
import re
import subprocess
import json
import sys
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel


@dataclass
class ToolCallCount:
    tool_name: str
    count: int


@dataclass
class TokenMetrics:
    total_input: int = 0
    total_output: int = 0
    total_reasoning: int = 0
    cache_read: int = 0
    cache_write: int = 0
    total_cost: int = 0  # in cents


@dataclass
class SessionMetrics:
    session_id: str
    agent: str
    model: str
    messages: int
    user_messages: int
    assistant_messages: int
    duration: str
    tool_calls: int
    tools_per_message: float
    compressions: int
    token_metrics: TokenMetrics
    tool_call_breakdown: List[ToolCallCount]


def run_opencode_command(args: List[str]) -> Dict[str, Any]:
    """Run opencode CLI command and return JSON output."""
    try:
        result = subprocess.run(
            ['opencode'] + args,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            raise RuntimeError(f"Command failed: {result.stderr}")
        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        raise RuntimeError("Command timed out")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse JSON: {e}")


def get_current_session_id() -> Optional[str]:
    """Get current session ID using opencode CLI."""
    try:
        sessions = run_opencode_command(['session', 'list', '--format', 'json'])
        if sessions and len(sessions) > 0:
            return sessions[0]['id']
        return None
    except Exception as e:
        print(f"Warning: Failed to get current session: {e}", file=sys.stderr)
        return None


def export_session(session_id: str) -> Dict[str, Any]:
    """Export session data using opencode CLI."""
    try:
        result = subprocess.run(
            ['opencode', 'export', session_id],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode != 0:
            raise RuntimeError(f"Export failed: {result.stderr}")
        # Find where JSON starts (after "Exporting session:" message)
        lines = result.stdout.split('\n')
        json_start = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('{') or line.strip().startswith('['):
                json_start = i
                break
        return json.loads('\n'.join(lines[json_start:]))
    except subprocess.TimeoutExpired:
        raise RuntimeError("Export timed out")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse export JSON: {e}")


def extract_tool_calls_from_parts(parts: List[Dict[str, Any]]) -> List[str]:
    """Extract tool calls from message parts."""
    tools = []
    for part in parts:
        if part.get('type') == 'tool':
            tool_name = part.get('tool', '')
            if tool_name:
                tools.append(tool_name)
        elif part.get('type') == 'text':
            # Also check for [tool: name] pattern in text
            text = part.get('text', '')
            matches = re.findall(r'\[tool:\s*(\w+)\]', text)
            tools.extend(matches)
    return tools


def count_tool_calls(messages: List[Dict[str, Any]]) -> List[ToolCallCount]:
    """Count tool calls by type."""
    counts: Dict[str, int] = {}

    for msg in messages:
        info = msg.get('info', {})
        if info.get('role') == 'assistant':
            parts = msg.get('parts', [])
            tools = extract_tool_calls_from_parts(parts)
            for tool in tools:
                counts[tool] = counts.get(tool, 0) + 1

    return [
        ToolCallCount(tool_name=tool_name, count=count)
        for tool_name, count in sorted(counts.items(), key=lambda x: x[1], reverse=True)
    ]


def calculate_duration(messages: List[Dict[str, Any]]) -> str:
    """Calculate session duration from messages."""
    if len(messages) < 2:
        return 'N/A'

    first_msg = messages[0].get('info', {})
    last_msg = messages[-1].get('info', {})

    first_time = first_msg.get('time', {}).get('created', 0)
    last_time = last_msg.get('time', {}).get('created', 0)

    if not first_time or not last_time:
        return 'N/A'

    duration_ms = last_time - first_time
    duration_sec = int(duration_ms / 1000)
    duration_min = int(duration_sec / 60)

    if duration_min > 0:
        remaining_sec = duration_sec % 60
        return f'{duration_min}m {remaining_sec}s'
    return f'{duration_sec}s'


def format_number(num: int) -> str:
    """Format large numbers."""
    if num >= 1000000:
        return f'{num / 1000000:.1f}M'
    if num >= 1000:
        return f'{num / 1000:.1f}K'
    return str(num)


def format_currency(cents: int) -> str:
    """Format currency from cents."""
    dollars = cents / 100
    if dollars >= 100:
        return f'${dollars:.0f}'
    if dollars >= 1:
        return f'${dollars:.2f}'
    return f'${dollars:.4f}'


def generate_report(metrics: SessionMetrics) -> str:
    """Generate the analysis report in Markdown format."""
    lines = []

    lines.append('## 📊 Session Usage Report')
    lines.append(f'\n**Session:** `{metrics.session_id}` | **Duration:** {metrics.duration} | **Agent:** {metrics.agent} | **Model:** {metrics.model}\n')

    lines.append('### Resumo\n')
    lines.append('| Métrica | Valor |')
    lines.append('|---|---|')
    lines.append(f'| Mensagens | {metrics.messages} ({metrics.user_messages} user / {metrics.assistant_messages} assistant) |')
    lines.append(f'| Tool calls | {metrics.tool_calls} |')
    lines.append(f'| Tools por mensagem (assistant) | {metrics.tools_per_message:.2f} avg |')
    lines.append(f'| Compressões DCP | {metrics.compressions} |\n')

    lines.append('### Token Metrics\n')
    lines.append('| Métrica | Valor |')
    lines.append('|---|---|')
    lines.append(f'| Input tokens | {format_number(metrics.token_metrics.total_input)} |')
    lines.append(f'| Output tokens | {format_number(metrics.token_metrics.total_output)} |')
    lines.append(f'| Reasoning tokens | {format_number(metrics.token_metrics.total_reasoning)} |')
    lines.append(f'| Cache read | {format_number(metrics.token_metrics.cache_read)} |')
    lines.append(f'| Cache write | {format_number(metrics.token_metrics.cache_write)} |')
    lines.append(f'| **Custo total** | **{format_currency(metrics.token_metrics.total_cost)}** |\n')

    if metrics.tool_call_breakdown:
        lines.append('### Top Tools\n')
        lines.append('| Tool | Calls |')
        lines.append('|---|---|')
        for tool in metrics.tool_call_breakdown[:10]:
            lines.append(f'| `{tool.tool_name}` | {tool.count} |')
        lines.append('')

    lines.append('### ⚠️ Gargalos Identificados\n')
    lines.append('*Análise baseada nos dados coletados.*\n')

    issues = []
    if metrics.tool_calls / max(metrics.assistant_messages, 1) > 5:
        issues.append(f'- **Tool spam:** {metrics.tool_calls / max(metrics.assistant_messages, 1):.1f} tool calls por mensagem de assistant → possível loop ou query mal formulada')
    if metrics.compressions > 3:
        issues.append(f'- **Context pressure:** {metrics.compressions} compressões DCP → sessão acumulou ruído excessivo')
    if metrics.token_metrics.total_cost > 100:
        issues.append(f'- **High cost:** {format_currency(metrics.token_metrics.total_cost)} → revisar necessidade de contexto extenso ou reasoning')

    if issues:
        lines.extend(issues)
        lines.append('')
    else:
        lines.append('- Nenhum gargalo crítico identificado.\n')

    lines.append('### ✅ Otimizações Sugeridas\n')
    lines.append('*Otimizações baseadas nos padrões observados.*\n')

    suggestions = []
    if metrics.token_metrics.cache_read > 0:
        cache_hit_rate = metrics.token_metrics.cache_read / max(metrics.token_metrics.total_input, 1)
        suggestions.append(f'- **Cache hit rate:** {cache_hit_rate:.1%} → cache está funcionando bem, continue usando')
    else:
        suggestions.append('- **Enable cache:** Configure cache com TTL para reduzir custos de input repetitivo')

    if metrics.tool_calls / max(metrics.assistant_messages, 1) > 3:
        suggestions.append('- **Reduce tool calls:** Considere consolidar operações ou usar `head_limit` em grep/search')

    suggestions.extend([
        '- **Use background_output:** Para subagents longos, use execução assíncrona',
        '- **Proactive compression:** Comprima seções já resolvidas para liberar contexto',
        '- **LSP diagnostics:** Use `lsp_diagnostics` em vez de builds completos quando possível',
    ])

    for suggestion in suggestions:
        lines.append(f'- {suggestion}')
    lines.append('')

    return '\n'.join(lines)


def print_rich_report(metrics: SessionMetrics):
    """Print the report using rich for nice terminal output."""
    console = Console()

    console.print(Panel.fit(
        f"[bold cyan]📊 Session Usage Report[/bold cyan]\n\n"
        f"Session: [yellow]{metrics.session_id}[/yellow] | "
        f"Duration: [green]{metrics.duration}[/green] | "
        f"Agent: [magenta]{metrics.agent}[/magenta]\n"
        f"Model: [cyan]{metrics.model}[/cyan]",
        title="Session Analysis",
        border_style="bright_blue"
    ))

    summary_table = Table(title="Resumo", show_header=True, header_style="bold magenta")
    summary_table.add_column("Métrica", style="cyan")
    summary_table.add_column("Valor", style="green")
    summary_table.add_row("Mensagens", f"{metrics.messages} ({metrics.user_messages} user / {metrics.assistant_messages} assistant)")
    summary_table.add_row("Tool calls", str(metrics.tool_calls))
    summary_table.add_row("Tools por mensagem", f"{metrics.tools_per_message:.2f} avg")
    summary_table.add_row("Compressões DCP", str(metrics.compressions))
    console.print(summary_table)
    console.print()

    token_table = Table(title="Token Metrics", show_header=True, header_style="bold magenta")
    token_table.add_column("Métrica", style="cyan")
    token_table.add_column("Valor", style="green")
    token_table.add_row("Input tokens", format_number(metrics.token_metrics.total_input))
    token_table.add_row("Output tokens", format_number(metrics.token_metrics.total_output))
    token_table.add_row("Reasoning tokens", format_number(metrics.token_metrics.total_reasoning))
    token_table.add_row("Cache read", format_number(metrics.token_metrics.cache_read))
    token_table.add_row("Cache write", format_number(metrics.token_metrics.cache_write))
    token_table.add_row("[bold]Custo total[/bold]", f"[bold green]{format_currency(metrics.token_metrics.total_cost)}[/bold green]")
    console.print(token_table)

    if metrics.tool_call_breakdown:
        tools_table = Table(title="Top Tools", show_header=True, header_style="bold magenta")
        tools_table.add_column("Tool", style="cyan")
        tools_table.add_column("Calls", style="green")
        for tool in metrics.tool_call_breakdown[:10]:
            tools_table.add_row(f"`{tool.tool_name}`", str(tool.count))
        console.print(tools_table)

    console.print("\n[bold yellow]⚠️ Gargalos Identificados[/bold yellow]")
    if metrics.tool_calls / max(metrics.assistant_messages, 1) > 5:
        console.print(f"[red]• Tool spam: {metrics.tool_calls / max(metrics.assistant_messages, 1):.1f} tool calls/assist msg[/red]")
    if metrics.compressions > 3:
        console.print(f"[red]• Context pressure: {metrics.compressions} DCP compressions[/red]")
    if metrics.token_metrics.total_cost > 100:
        console.print(f"[red]• High cost: {format_currency(metrics.token_metrics.total_cost)}[/red]")
    console.print("[dim]Análise baseada nos dados coletados.[/dim]\n")

    console.print("[bold green]✅ Otimizações Sugeridas[/bold green]")
    console.print("[dim]Otimizações baseadas nos padrões observados.[/dim]\n")


def analyze_session(session_id: Optional[str] = None, output_format: str = "markdown") -> str:
    """Main analysis function using opencode export."""
    if not session_id:
        session_id = get_current_session_id()
        if not session_id:
            raise ValueError('No current session found. Please provide a session ID.')

    print(f"Exporting session {session_id}...", file=sys.stderr)
    session_data = export_session(session_id)

    info = session_data.get('info', {})
    messages = session_data.get('messages', [])

    if not messages:
        raise RuntimeError(f"No messages found in session {session_id}")

    user_messages = sum(1 for m in messages if m.get('info', {}).get('role') == 'user')
    assistant_messages = sum(1 for m in messages if m.get('info', {}).get('role') == 'assistant')

    tool_call_breakdown = count_tool_calls(messages)
    duration = calculate_duration(messages)

    compressions = 0
    for m in messages:
        msg_info = m.get('info', {})
        if msg_info.get('summary') is True:
            compressions += 1
        for part in m.get('parts', []):
            if part.get('type') == 'tool' and part.get('tool') == 'compress':
                compressions += 1
                break

    token_metrics = TokenMetrics()
    for m in messages:
        msg_info = m.get('info', {})
        if msg_info.get('role') == 'assistant':
            tokens = msg_info.get('tokens', {})
            token_metrics.total_input += tokens.get('input', 0)
            token_metrics.total_output += tokens.get('output', 0)
            token_metrics.total_reasoning += tokens.get('reasoning', 0)
            cache = tokens.get('cache', {})
            token_metrics.cache_read += cache.get('read', 0)
            token_metrics.cache_write += cache.get('write', 0)
            token_metrics.total_cost += msg_info.get('cost', 0)

    model_info = info.get('model', {})
    model = model_info.get('id', 'Unknown')

    metrics = SessionMetrics(
        session_id=session_id,
        agent=info.get('agent', 'Unknown'),
        model=model,
        messages=len(messages),
        user_messages=user_messages,
        assistant_messages=assistant_messages,
        duration=duration,
        tool_calls=sum(t.count for t in tool_call_breakdown),
        tools_per_message=(sum(t.count for t in tool_call_breakdown) / assistant_messages) if assistant_messages > 0 else 0,
        compressions=compressions,
        token_metrics=token_metrics,
        tool_call_breakdown=tool_call_breakdown,
    )

    if output_format == "markdown":
        return generate_report(metrics)
    elif output_format == "terminal":
        print_rich_report(metrics)
        return ""
    else:
        raise ValueError(f"Unsupported output format: {output_format}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Analyze opencode session token usage'
    )
    parser.add_argument(
        'session_id',
        nargs='?',
        help='Session ID to analyze (default: current session)'
    )
    parser.add_argument(
        '--format', '-f',
        choices=['markdown', 'terminal'],
        default='markdown',
        help='Output format (default: markdown)'
    )

    args = parser.parse_args()

    try:
        report = analyze_session(args.session_id, args.format)
        if report:
            print(report)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

#!/usr/bin/env node
/**
 * Session Usage Analyzer Workflow
 *
 * Analyzes token consumption in opencode sessions using the SDK.
 * More deterministic and faster than skill-based approach.
 */

import { createOpencodeClient, OpencodeClient } from '@opencode-ai/sdk';

interface ToolCallCount {
  toolName: string;
  count: number;
}

interface SessionMetrics {
  sessionId: string;
  agent: string;
  messages: number;
  userMessages: number;
  assistantMessages: number;
  duration: string;
  toolCalls: number;
  toolsPerMessage: number;
  compressions: number;
  tokenMetrics: {
    totalInput: number;
    totalOutput: number;
    totalReasoning: number;
    cacheRead: number;
    cacheWrite: number;
    totalCost: number;
  };
  toolCallBreakdown: ToolCallCount[];
}

/**
 * Parse tool calls from assistant messages
 */
function extractToolCalls(assistantMsg: any): string[] {
  const tools: string[] = [];
  if (assistantMsg.content) {
    const matches = assistantMsg.content.matchAll(/\[tool:\s*(\w+)\]/g);
    for (const match of matches) {
      tools.push(match[1]);
    }
  }
  return tools;
}

/**
 * Count tool calls by type
 */
function countToolCalls(messages: any[]): ToolCallCount[] {
  const counts: Record<string, number> = {};

  for (const msg of messages) {
    if (msg.role === 'assistant') {
      const tools = extractToolCalls(msg);
      for (const tool of tools) {
        counts[tool] = (counts[tool] || 0) + 1;
      }
    }
  }

  return Object.entries(counts)
    .map(([toolName, count]) => ({ toolName, count }))
    .sort((a, b) => b.count - a.count);
}

/**
 * Calculate session duration
 */
function calculateDuration(messages: any[]): string {
  if (messages.length < 2) return 'N/A';

  const firstTime = messages[0].time?.created || 0;
  const lastTime = messages[messages.length - 1].time?.created || 0;

  const durationMs = lastTime - firstTime;
  const durationSec = Math.floor(durationMs / 1000);
  const durationMin = Math.floor(durationSec / 60);

  if (durationMin > 0) {
    const remainingSec = durationSec % 60;
    return `${durationMin}m ${remainingSec}s`;
  }
  return `${durationSec}s`;
}

/**
 * Format large numbers
 */
function formatNumber(num: number): string {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
  return num.toString();
}

/**
 * Format currency
 */
function formatCurrency(cents: number): string {
  const dollars = cents / 100;
  if (dollars >= 100) return `$${dollars.toFixed(0)}`;
  if (dollars >= 1) return `$${dollars.toFixed(2)}`;
  return `$${dollars.toFixed(4)}`;
}

/**
 * Generate the analysis report
 */
function generateReport(metrics: SessionMetrics): string {
  const lines: string[] = [];

  lines.push('## 📊 Session Usage Report');
  lines.push(`\n**Session:** \`${metrics.sessionId}\` | **Duration:** ${metrics.duration} | **Agent:** ${metrics.agent}\n`);
  lines.push('### Resumo\n');
  lines.push('| Métrica | Valor |');
  lines.push('|---|---|');
  lines.push(`| Mensagens | ${metrics.messages} (${metrics.userMessages} user / ${metrics.assistantMessages} assistant) |`);
  lines.push(`| Tool calls | ${metrics.toolCalls} |`);
  lines.push(`| Tools por mensagem (assistant) | ${metrics.toolsPerMessage.toFixed(2)} avg |`);
  lines.push(`| Compressões DCP | ${metrics.compressions} |\n`);

  lines.push('### Token Metrics\n');
  lines.push('| Métrica | Valor |');
  lines.push('|---|---|');
  lines.push(`| Input tokens | ${formatNumber(metrics.tokenMetrics.totalInput)} |`);
  lines.push(`| Output tokens | ${formatNumber(metrics.tokenMetrics.totalOutput)} |`);
  lines.push(`| Reasoning tokens | ${formatNumber(metrics.tokenMetrics.totalReasoning)} |`);
  lines.push(`| Cache read | ${formatNumber(metrics.tokenMetrics.cacheRead)} |`);
  lines.push(`| Cache write | ${formatNumber(metrics.tokenMetrics.cacheWrite)} |`);
  lines.push(`| **Custo total** | **${formatCurrency(metrics.tokenMetrics.totalCost)}** |\n`);

  if (metrics.toolCallBreakdown.length > 0) {
    lines.push('### Top Tools\n');
    lines.push('| Tool | Calls |');
    lines.push('|---|---|');
    for (const tool of metrics.toolCallBreakdown.slice(0, 10)) {
      lines.push(`| \`${tool.toolName}\` | ${tool.count} |`);
    }
    lines.push('');
  }

  lines.push('### ⚠️ Gargalos Identificados\n');
  lines.push('*Análise baseada nos dados coletados.*\n');

  lines.push('### ✅ Otimizações Sugeridas\n');
  lines.push('*Otimizações baseadas nos padrões observados.*\n');

  return lines.join('\n');
}

/**
 * Main analysis function
 */
export async function analyzeSession(sessionId?: string): Promise<string> {
  const client = createOpencodeClient({
    baseUrl: 'http://localhost:4100',
  });

  if (!sessionId) {
    const sessionList = await client.session.list();
    const currentSession = sessionList.data?.find((s: any) => s.isCurrent);
    if (!currentSession) {
      throw new Error('No current session found');
    }
    sessionId = currentSession.id;
  }

  const sessionInfo = await client.session.get({ params: { id: sessionId } });
  const info = sessionInfo.data;

  const messagesResponse = await client.session.messages({
    params: { id: sessionId },
    query: { includeTranscript: true },
  });
  const messages = messagesResponse.data || [];

  const userMessages = messages.filter((m: any) => m.role === 'user').length;
  const assistantMessages = messages.filter((m: any) => m.role === 'assistant').length;
  const toolCallBreakdown = countToolCalls(messages);
  const duration = calculateDuration(messages);

  const compressions = messages.filter((m: any) => m.summary === true).length;

  let totalInput = 0;
  let totalOutput = 0;
  let totalReasoning = 0;
  let cacheRead = 0;
  let cacheWrite = 0;
  let totalCost = 0;

  for (const msg of messages) {
    if (msg.role === 'assistant' && msg.tokens) {
      totalInput += msg.tokens.input || 0;
      totalOutput += msg.tokens.output || 0;
      totalReasoning += msg.tokens.reasoning || 0;
      cacheRead += msg.tokens.cache?.read || 0;
      cacheWrite += msg.tokens.cache?.write || 0;
      totalCost += msg.cost || 0;
    }
  }

  const metrics: SessionMetrics = {
    sessionId,
    agent: info.agent || 'Unknown',
    messages: messages.length,
    userMessages,
    assistantMessages,
    duration,
    toolCalls: toolCallBreakdown.reduce((sum, t) => sum + t.count, 0),
    toolsPerMessage: assistantMessages > 0 ? (toolCallBreakdown.reduce((sum, t) => sum + t.count, 0) / assistantMessages) : 0,
    compressions,
    tokenMetrics: {
      totalInput,
      totalOutput,
      totalReasoning,
      cacheRead,
      cacheWrite,
      totalCost,
    },
    toolCallBreakdown,
  };

  return generateReport(metrics);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const sessionId = process.argv[2];
  analyzeSession(sessionId)
    .then((report) => {
      console.log(report);
      process.exit(0);
    })
    .catch((error) => {
      console.error('Error:', error.message);
      process.exit(1);
    });
}

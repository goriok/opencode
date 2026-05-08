---
name: session-usage-analyzer
description: Analisa consumo de tokens da sessão opencode atual, identifica gargalos, sugere otimizações e avalia problemas de custo. Invocar quando o usuário pedir para analisar sessão, consumo de tokens, custo, otimizar uso, ou "quanto estou gastando".
argument-hint: "[session-id|current]"
---

# Session Usage Analyzer

Analisa a sessão opencode atual (ou uma específica) para extrair dados reais de consumo de tokens, identificar padrões ineficientes e sugerir otimizações.

Esta skill invoca um workflow Python determinístico que usa o LiteLLM provider para obter dados precisos de token consumption, sem depender de estimativas heurísticas.

## Fluxo de Análise

### 1. Pré-requisitos

Verifique se o LiteLLM proxy está rodando:

```bash
oc litellm status
```

Se não estiver rodando, inicie:

```bash
oc litellm up
```

### 2. Executar o Workflow Python

O workflow `session-usage-analyzer.py` está localizado em `~/.config/opencode/workflows/`.

Para a sessão atual:

```bash
cd ~/.config/opencode/workflows
python session-usage-analyzer.py --format markdown
```

Para uma sessão específica:

```bash
python session-usage-analyzer.py ses_abc123def456 --format markdown
```

### 3. Formatar e Apresentar o Relatório

O workflow gera um relatório Markdown completo com:

- **Resumo**: mensagens, tool calls, compressões
- **Token Metrics**: input/output/reasoning, cache, custo total (dados reais)
- **Top Tools**: ranking de ferramentas mais utilizadas
- **Gargalos Identificados**: análise baseada em métricas reais
- **Otimizações Sugeridas**: recomendações baseadas em padrões observados

Apresente o relatório completo ao usuário.

## Análise de Eficiência (Baseada em Dados Reais)

O workflow calcula métricas reais do LiteLLM provider. Ao apresentar o relatório, destaque:

### Gargalos (investigar)

- **Tool spam**: >5 tool calls por mensagem → possível loop ou query mal formulada
- **Output desperdiçado**: grep/read com >100 resultados → usar `head_limit` ou `limit`
- **Context pressure**: >3 compressões → sessão acumulou ruído excessivo
- **Subagent explosion**: >10 spawns → delegação granular demais
- **Duração longa**: sessão >60min com <20 mensagens → idle ou bloqueado
- **Custo elevado**: custos totais >$5 para uma sessão

### Boas práticas (recomendar)

- Usar `grep` com `head_limit: 20` em vez de search sem limite
- Usar `session_search` em vez de `session_read` completo para buscar algo específico
- Comprimir proativamente seções já resolvidas
- Usar `mcp_lazy: true` (já ativo) — poupa ~32k tokens por sessão
- Preferir `lsp_diagnostics` em vez de rodar build completo
- Usar `background_output` para subagents em vez de sync

## Formato de Saída

O workflow gera relatório Markdown no seguinte formato:

```markdown
## 📊 Session Usage Report

**Session:** `ses_xyz` | **Duration:** 5m 30s | **Agent:** Ada Lovelace

### Resumo
| Métrica | Valor |
|---|---|
| Mensagens | 22 (10 user / 12 assistant) |
| Tool calls | 15 (avg 1.25/msg) |
| Tools por mensagem (assistant) | 1.25 avg |
| Compressões DCP | 1 |

### Token Metrics
| Métrica | Valor |
|---|---|
| Input tokens | 12.5K |
| Output tokens | 8.3K |
| Reasoning tokens | 2.1K |
| Cache read | 3.2K |
| Cache write | 1.1K |
| **Custo total** | **$0.45** |

### Top Tools
| Tool | Calls |
|---|---|
| `grep` | 5 |
| `read` | 4 |
| `bash` | 3 |

### ⚠️ Gargalos Identificados
*Análise baseada nos dados coletados.*

### ✅ Otimizações Sugeridas
*Otimizações baseadas nos padrões observados.*
```

## Regras

- **Use o workflow Python sempre** - ele fornece dados reais do LiteLLM, não estimativas
- Verifique se o LiteLLM está rodando antes de executar o workflow
- Se o workflow falhar com erro de conexão, instrua o usuário a iniciar o LiteLLM
- Não tente usar heurísticas ou estimativas - o workflow fornece dados precisos
- Apresente o relatório completo gerado pelo workflow sem modificação
- Os dados reais do LiteLLM sempre são mais confiáveis do que qualquer estimativa

## Dependências do Workflow

O workflow Python requer:
- Python 3.10+
- httpx (cliente HTTP)
- pydantic (validação de dados)
- rich (formatação de terminal)

Instalação: `pip install httpx pydantic rich` (ou via `pip install -e pyproject.toml`)

## Referências

- Workflow: `~/.config/opencode/workflows/session-usage-analyzer.py`
- README do workflow: `~/.config/opencode/workflows/README-session-usage-analyzer.md`
- Config do projeto: `~/.config/opencode/workflows/pyproject.toml`

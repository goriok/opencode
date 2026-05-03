# OpenCode Go — Guia de Modelos e Melhores Utilizações

> **Assinatura:** US$ 5 (1º mês) / US$ 10/mês — modelos abertos curados para programação
>
> **Referência:** [opencode.ai/docs/pt-br/go](https://opencode.ai/docs/pt-br/go) | Atualizado: Abril 2026

---

## Visão Geral

O OpenCode Go é um plano de assinatura que oferece **14 modelos abertos de programação** hospedados em US, EU e Singapura, testados e com benchmark pela equipe do OpenCode.

### Como referenciar na config

```
opencode-go/<model-id>
```

Exemplo: `opencode-go/deepseek-v4-pro`, `opencode-go/kimi-k2.6`

---

## Modelos Disponíveis

### Tabela Resumo

| Modelo | Reqs/5h | Reqs/mês | API Protocol | Destaque |
|---|---|---|---|---|
| **GLM-5.1** | 880 | 4.300 | OpenAI-compat | Máxima capacidade |
| **GLM-5** | 1.150 | 5.750 | OpenAI-compat | Capacidade sólida |
| **Kimi K2.6** | 1.150 | 5.750 | OpenAI-compat | Equilibrado novo |
| **Kimi K2.5** | 1.850 | 9.250 | OpenAI-compat | Bom custo-benefício |
| **DeepSeek V4 Pro** | 1.300 | 6.500 | Anthropic-compat | Qualidade alta, tool-use |
| **DeepSeek V4 Flash** | 7.450 | 37.300 | Anthropic-compat | Velocidade + tool-use |
| **MiMo-V2-Pro** | 1.290 | 6.450 | OpenAI-compat | Mid-range sólido |
| **MiMo-V2.5-Pro** | 1.290 | 6.450 | OpenAI-compat | Mid-range atualizado |
| **MiMo-V2-Omni** | 2.150 | 10.900 | OpenAI-compat | Omnimodal |
| **MiMo-V2.5** | 2.150 | 10.900 | OpenAI-compat | Econômico |
| **MiniMax M2.7** | 3.400 | 17.000 | Anthropic-compat | Budget, tool-use |
| **MiniMax M2.5** | 6.300 | 31.800 | Anthropic-compat | Campeão de economia |
| **Qwen3.6 Plus** | 3.300 | 16.300 | Alibaba-compat | Capacidade + volume |
| **Qwen3.5 Plus** | 10.200 | 50.500 | Alibaba-compat | Máximo volume |

---

## Tiers de Uso Recomendado

### Tier A — Tarefas Complexas (arquitetura, análise profunda, debugging difícil)

| Modelo | Por quê? |
|---|---|
| **GLM-5.1** | Maior capacidade entre os modelos Go. Ideal para refatorações complexas, design de arquitetura, análise multi-arquivo |
| **DeepSeek V4 Pro** ⭐ | Protocolo Anthropic → tool-use robusto. Melhor para agentes que usam muitas ferramentas (MCP, LSP, bash). É o mais indicado para tarefas de coding complexo com tool calling |
| **Kimi K2.6** | Versão mais recente da linha Kimi. Boa para código que exige raciocínio multi-etapas |

### Tier B — Daily Driver (tarefas do dia a dia, features, refactors médios)

| Modelo | Por quê? |
|---|---|
| **Kimi K2.5** | Excelente relação capacidade/custo. 1.850 req/5h permite uso intensivo sem preocupação |
| **GLM-5** | Versão anterior do GLM-5.1, ainda muito capaz. Bom para quando GLM-5.1 está sobrecarregado como fallback |
| **Qwen3.6 Plus** | Boa capacidade com volume generoso (3.300 req/5h). Ideal para sessões longas |
| **MiMo-V2.5-Pro** | Mid-range atualizado, balanceado |

### Tier C — Tarefas Rápidas (lookups, correções pontuais, scaffolding)

| Modelo | Por quê? |
|---|---|
| **DeepSeek V4 Flash** ⭐ | Rápido com tool-use Anthropic. 7.450 req/5h. Ideal para fixes rápidos, explicações de código, comandos simples |
| **MiniMax M2.7** | Econômico com tool-use Anthropic. 3.400 req/5h. Bom para tarefas repetitivas |
| **Qwen3.5 Plus** | Máximo volume: 10.200 req/5h. Perfeito para tarefas triviais, geração de boilerplate |
| **MiMo-V2.5** | 2.150 req/5h, boa velocidade |

### Tier D — Especializado

| Modelo | Por quê? |
|---|---|
| **MiMo-V2-Omni** | Omnimodal — provável suporte a imagem. Útil para tarefas que envolvem screenshots, diagramas, ou análise visual de UI |
| **MiniMax M2.5** | 6.300 req/5h. Segundo mais econômico, Anthropic API (tool-use). Bom fallback barato com tool calling |

---

## Mapeamento com Agentes (oh-my-openagent)

Com base na sua configuração atual em `oh-my-openagent.jsonc`:

| Agente | Modelo | Por quê? |
|---|---|---|
| **alan-turing** (SDLC) | `deepseek-v4-pro` + thinking | Orquestração pesada, precisa de raciocínio profundo |
| **grace-hopper** (troubleshoot) | `deepseek-v4-pro` + thinking | Diagnóstico complexo com thinking |
| **margaret-hamilton** (análise) | `deepseek-v4-pro` + thinking | ATAM/ISO-25010 requer thinking profundo |
| **ada-lovelace** (exploração) | `deepseek-v4-flash` | Investigação rápida, alto volume |
| **maestro** (meta-orchestrator) | `glm-5.1` | Classificação de intenção, capacidade sólida |
| **oracle** (code review) | `deepseek-v4-pro` + thinking | Análise profunda de código |
| **sisyphus** (daily driver) | `kimi-k2.5` | Alto volume + boa qualidade (9.2K req/mês) |
| **explore** (busca) | `qwen3.5-plus` | Máximo volume para exploração (50.5K req/mês) |

### Exemplo de config

```jsonc
// oh-my-openagent.jsonc
"agents": {
  "alan-turing":       { "model": "opencode-go/deepseek-v4-pro", "thinking": { "type": "enabled" } },
  "grace-hopper":      { "model": "opencode-go/deepseek-v4-pro", "thinking": { "type": "enabled" } },
  "margaret-hamilton": { "model": "opencode-go/deepseek-v4-pro", "thinking": { "type": "enabled" } },
  "ada-lovelace":      { "model": "opencode-go/deepseek-v4-flash" },
  "maestro":           { "model": "opencode-go/glm-5.1" },
  "sisyphus":          { "model": "opencode-go/kimi-k2.5" },
  "explore":           { "model": "opencode-go/qwen3.5-plus" }
}
```

---

## Variantes Disponíveis

### Anthropic-compatible (DeepSeek V4, MiniMax M2.x)

- `high` — orçamento de thinking alto (padrão)
- `max` — orçamento de thinking máximo

### OpenAI-compatible (GLM, Kimi, MiMo, Qwen)

- `low` — baixo esforço de raciocínio
- `medium` — esforço médio
- `high` — alto esforço
- `xhigh` — esforço extra alto

Uso via TUI: `variant_cycle` para alternar rapidamente.

---

## Estratégia de Uso Recomendada

```
┌─────────────────────────────────────────────────────────┐
│  Inicie com Kimi K2.6 (daily driver)                     │
│  └─ Se precisar de tool-use complexo → DeepSeek V4 Pro  │
│  └─ Se for tarefa trivial/rápida → DeepSeek V4 Flash    │
│  └─ Se orçamento estiver acabando → MiniMax M2.5        │
│  └─ Se precisar de máxima capacidade → GLM-5.1          │
│                                                          │
│  Seu limite mensal: US$ 60 (~6.500 reqs com V4 Pro)     │
│  Acompanhe em: opencode.ai/auth                          │
└─────────────────────────────────────────────────────────┘
```

---

## Limites de Uso

| Limite | Valor | Descrição |
|---|---|---|
| **5 horas** | US$ 12 | Rolling window, protege contra picos |
| **Semanal** | US$ 30 | Reset a cada semana |
| **Mensal** | US$ 60 | Total do plano Go |

**Dica:** Se atingir o limite, ative **"Use balance"** no console para fallback automático para créditos Zen.

---

## Privacidade

- Política de **retenção zero** — dados não são usados para treinamento
- Modelos hospedados em US, EU e Singapura
- Acesso via API padrão (OpenAI-compat ou Anthropic-compat)

---

## Glossário de IDs de Modelo

| Nome | ID para config |
|---|---|
| GLM-5.1 | `glm-5.1` |
| GLM-5 | `glm-5` |
| Kimi K2.5 | `kimi-k2.5` |
| Kimi K2.6 | `kimi-k2.6` |
| DeepSeek V4 Pro | `deepseek-v4-pro` |
| DeepSeek V4 Flash | `deepseek-v4-flash` |
| MiMo-V2-Pro | `mimo-v2-pro` |
| MiMo-V2-Omni | `mimo-v2-omni` |
| MiMo-V2.5-Pro | `mimo-v2.5-pro` |
| MiMo-V2.5 | `mimo-v2.5` |
| MiniMax M2.7 | `minimax-m2.7` |
| MiniMax M2.5 | `minimax-m2.5` |
| Qwen3.6 Plus | `qwen3.6-plus` |
| Qwen3.5 Plus | `qwen3.5-plus` |

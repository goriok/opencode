# OpenCode Go - Technical Usage Guide

> Maximize your subscription through strategic model selection, quota management, and cost-efficient usage patterns.

---

## 1. Model Catalog

### Available Models

OpenCode Go provides access to 14 curated open-source coding models, tested and benchmarked by the OpenCode team for agent-grade coding performance.

#### Tier 1: Flagship Models (highest capability, lowest request volume)

| Model | Best For | Relative Cost |
|-------|----------|---------------|
| **GLM-5.1** | Long-horizon agentic tasks, complex engineering | Highest |
| **GLM-5** | General coding, strong reasoning | High |
| **Kimi K2.6** | Balanced coding + reasoning | High |
| **DeepSeek V4 Pro** | Code generation, complex tasks | Medium-High |

#### Tier 2: High-Value Models (great capability-to-cost ratio)

| Model | Best For | Relative Cost |
|-------|----------|---------------|
| **Kimi K2.5** | Coding tasks, fast iteration | Medium |
| **MiMo-V2-Pro** | Multi-step reasoning | Medium |
| **MiMo-V2.5-Pro** | Multi-step reasoning (improved) | Medium |
| **Qwen3.6 Plus** | General coding, balanced | Medium |
| **MiniMax M2.7** | Fast coding, good quality | Low-Medium |

#### Tier 3: High-Volume Models (best for routine work)

| Model | Best For | Relative Cost |
|-------|----------|---------------|
| **MiMo-V2-Omni** | General tasks, multimodal | Low |
| **MiMo-V2.5** | General tasks, improved | Low |
| **MiniMax M2.5** | Quick edits, trivial tasks | Very Low |
| **Qwen3.5 Plus** | Bulk requests, simple tasks | Very Low |
| **DeepSeek V4 Flash** | Massive throughput, simple tasks | Minimal |

---

## 2. Usage Limits & Quota Economics

### Limit Structure

| Window | Dollar Limit | Notes |
|--------|-------------|-------|
| **5-hour rolling** | $12 | Resets 5 hours after consumption |
| **Weekly** | $30 | Resets every 7 days |
| **Monthly** | $60 | Hard cap |

Limits are defined in **dollar value**, not request count. Actual request count varies by model cost.

### Estimated Request Volumes

| Model | Per 5hr | Per Week | Per Month |
|-------|---------|----------|-----------|
| GLM-5.1 | 880 | 2,150 | 4,300 |
| GLM-5 | 1,150 | 2,880 | 5,750 |
| Kimi K2.6 | 1,150 | 2,880 | 5,750 |
| Kimi K2.5 | 1,850 | 4,630 | 9,250 |
| MiMo-V2-Pro | 1,290 | 3,225 | 6,450 |
| MiMo-V2.5-Pro | 1,290 | 3,225 | 6,450 |
| MiMo-V2-Omni | 2,150 | 5,450 | 10,900 |
| MiMo-V2.5 | 2,150 | 5,450 | 10,900 |
| MiniMax M2.7 | 3,400 | 8,500 | 17,000 |
| MiniMax M2.5 | 6,300 | 15,900 | 31,800 |
| Qwen3.6 Plus | 3,300 | 8,200 | 16,300 |
| Qwen3.5 Plus | 10,200 | 25,200 | 50,500 |
| DeepSeek V4 Pro | 3,450 | 8,550 | 17,150 |
| DeepSeek V4 Flash | 31,650 | 79,050 | 158,150 |

> Estimates based on typical coding agent patterns (700-1000 input tokens, 41K-82K cached tokens, 125-290 output tokens per request).

### Key Insight: Cost-per-Request Spectrum

```
DeepSeek V4 Flash  ←  14x more requests than GLM-5.1 for same dollar spend
Qwen3.5 Plus       ←  12x
MiniMax M2.5       ←   7x
MiMo-V2-Omni       ←   2.4x
Kimi K2.5          ←   2.1x
GLM-5              ←   1.3x
GLM-5.1            ←   1x (baseline)
```

---

## 3. Model Selection Strategy

### Decision Matrix

```
Task Complexity              Recommended Model
────────────────────────────────────────────────
Trivial edits / renames      DeepSeek V4 Flash or Qwen3.5 Plus
Simple refactors             Qwen3.5 Plus or MiniMax M2.5
Unit tests                   Qwen3.6 Plus or MiniMax M2.7
Feature implementation       MiMo-V2.5-Pro or Kimi K2.5
Multi-file changes           Kimi K2.5 or MiMo-V2-Pro
Complex debugging            Kimi K2.6 or DeepSeek V4 Pro
Architecture decisions       GLM-5 or Kimi K2.6
Long-horizon agentic tasks   GLM-5.1
Maximum throughput needed    DeepSeek V4 Flash
```

### Tiered Usage Strategy

**Daily driver pattern (maximize monthly quota):**

1. **80% of tasks** → `Qwen3.5 Plus` or `DeepSeek V4 Flash` (cheap, handles routine work)
2. **15% of tasks** → `Kimi K2.5` or `MiMo-V2.5-Pro` (moderate complexity)
3. **5% of tasks** → `GLM-5.1` (reserve for truly complex problems)

This pattern yields approximately **40,000-50,000 requests/month** instead of 4,300 if using GLM-5.1 exclusively.

### When to Use Each Flagship

| Model | Use When... | Avoid When... |
|-------|-------------|---------------|
| **GLM-5.1** | 8-hour sustained tasks, iterative optimization, complex engineering | Simple edits, quick questions |
| **GLM-5** | Strong reasoning needed, but task is under 2 hours | Trivial changes |
| **Kimi K2.6** | Balanced coding + reasoning, general feature work | Bulk operations |
| **DeepSeek V4 Pro** | Code generation, well-defined problems | Exploratory tasks |

---

## 4. API Access & Integration

### Unified Endpoint

All models use the same base endpoint with model-specific IDs:

```
https://opencode.ai/zen/go/v1/chat/completions
```

**Exception:** MiniMax models use the Anthropic-compatible endpoint:
```
https://opencode.ai/zen/go/v1/messages
```

### Model IDs for OpenCode Config

Use the format `opencode-go/<model-id>` in your OpenCode configuration:

```
opencode-go/deepseek-v4-flash
opencode-go/qwen3.5-plus
opencode-go/glm-5.1
opencode-go/kimi-k2.5
opencode-go/minimax-m2.7
```

### SDK Integration

All models support the `@ai-sdk/openai-compatible` package, except:
- **MiniMax M2.5 / M2.7** → `@ai-sdk/anthropic`
- **Qwen3.5 Plus / Qwen3.6 Plus** → `@ai-sdk/alibaba`

### Direct API Usage

```bash
curl -X POST "https://opencode.ai/zen/go/v1/chat/completions" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-v4-flash",
    "messages": [{"role": "user", "content": "Write a Python function..."}]
  }'
```

---

## 5. Quota Management Strategies

### Monitoring

Track current usage at [opencode.ai/auth](https://opencode.ai/auth).

### Optimization Tactics

1. **Use cached tokens aggressively** — most coding agent work is repetitive file reads. Caching is already factored into estimates but keeping context short reduces uncached input.

2. **Match model to task** — the biggest waste is using GLM-5.1 for a 3-line fix. Default to the cheapest model that can handle the task.

3. **Batch related changes** — one well-structured prompt is cheaper than five fragmented ones.

4. **Respect the 5-hour window** — the $12/5hr limit is the tightest constraint. If you hit it, you're locked out for 5 hours regardless of weekly/monthly headroom.

5. **Use free models after hitting limits** — when quota is exhausted, you can continue using free models available in OpenCode Zen.

### Balance Fallback

Enable **"Use balance"** in the console to fall back to Zen credits after hitting Go limits instead of blocking requests.

---

## 6. Regional Infrastructure

Models are hosted across **US, EU, and Singapore** for stable global access. This matters for:

- **Latency** — requests route to the nearest region automatically
- **Compliance** — zero-retention policy, no data used for training
- **Reliability** — multiple providers ensure failover capability

---

## 7. Comparison: When to Use Go vs Other Providers

### Use Go When

- You want predictable monthly costs with a hard cap
- You primarily use open-source models
- You need high-volume access to models like DeepSeek V4 Flash or Qwen3.5 Plus
- You want curated, benchmarked model/provider combinations

### Complement With Zen When

- You need proprietary models (GPT, Claude, Gemini)
- You need fine-grained pay-per-token billing
- You want free model options (Big Pickle, MiniMax M2.5 Free, etc.)

---

## 8. Quick Reference Card

```
BULK / TRIVIAL          → DeepSeek V4 Flash (158K/mo requests)
CHEAP ROUTINE            → Qwen3.5 Plus (50K/mo requests)
FAST FEATURE WORK        → Kimi K2.5 (9K/mo requests)
BALANCED DEVELOPMENT     → MiMo-V2.5-Pro (6.5K/mo requests)
STRONG REASONING         → GLM-5 or Kimi K2.6 (~5.7K/mo requests)
COMPLEX GENERATION       → DeepSeek V4 Pro (17K/mo requests)
LONG-HORIZON AGENTIC     → GLM-5.1 (4.3K/mo requests)

5-HOUR LIMIT             → $12 (tightest constraint)
WEEKLY LIMIT             → $30
MONTHLY LIMIT            → $60

MONITOR USAGE            → opencode.ai/auth
FALLBACK TO CREDITS      → Enable "Use balance" in console
FREE MODELS AFTER LIMIT  → Available via OpenCode Zen

ENDPOINT                → opencode.ai/zen/go/v1/chat/completions
MODEL ID FORMAT          → opencode-go/<model-id>
```

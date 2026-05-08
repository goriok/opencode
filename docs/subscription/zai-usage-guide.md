# GLM Coding Plan - Technical Usage Guide

> Maximize your coding subscription through strategic model selection, quota management, and MCP tool utilization.

---

## 1. Model Selection Strategy

### Available Models

| Model | Context | Max Output | Positioning | When to Use |
|-------|---------|------------|-------------|-------------|
| **GLM-5.1** | 200K | 128K | Flagship, rivals Claude Opus 4.6 | Complex reasoning, long-horizon tasks, agentic coding |
| **GLM-5-Turbo** | 200K | 128K | Fast flagship variant | Same as GLM-5.1 when speed matters |
| **GLM-4.7** | 128K | 16K | High-performance workhorse | Day-to-day development, most coding tasks |
| **GLM-4.5-Air** | 128K | 4K | Lightweight, fast | Quick queries, trivial edits, Haiku-tier tasks |

### Decision Matrix

```
Task Complexity                    Recommended Model
───────────────────────────────────────────────────────
Simple refactor / rename            GLM-4.5-Air (Haiku slot)
Unit test generation                GLM-4.7 (Sonnet/Opus slot)
Feature implementation              GLM-4.7
Complex debugging / multi-file      GLM-4.7
Architecture decisions              GLM-5.1
Long-horizon agentic tasks (>1hr)   GLM-5.1
Performance optimization            GLM-5.1
SWE-Bench level problems            GLM-5.1
```

### Key Insight: GLM-5.1 vs GLM-4.7

- **GLM-5.1** is designed for **8-hour sustained execution** with autonomous "experiment-analyze-optimize" loops. Use it when the task benefits from iterative refinement.
- **GLM-4.7** is the sweet spot for most development work — fast, capable, and costs **1×** quota at all times.
- Reserve GLM-5.1 for tasks where its long-horizon capability actually matters. Using it for simple edits is a quota waste.

---

## 2. Quota Management

### How Quota Works

- **5-hour rolling window**: quota resets 5 hours after consumption (not on a fixed schedule)
- **Weekly cap**: resets every 7 days from subscription activation
- **One prompt ≈ 15-20 model invocations** internally (auto-accept multiplies this)

### Quota Multipliers (GLM-5.1 / GLM-5-Turbo)

| Period | Multiplier | Impact |
|--------|------------|--------|
| **Off-peak** (all hours except 14:00-18:00 UTC+8) | 1× (promo until end of June) | Best value — use flagship here |
| **Peak** (14:00-18:00 UTC+8) | 3× | 3× quota burn — avoid if possible |
| **Off-peak** (normal, after promo) | 2× | Standard rate |

### Peak Hours Reference (UTC+8 → your timezone)

| UTC | UTC-3 (Brasilia) | Action |
|-----|-------------------|--------|
| 06:00 | 03:00 | Off-peak — ideal for flagship use |
| 14:00 | 11:00 | **Peak starts** — switch to GLM-4.7 |
| 18:00 | 15:00 | **Peak ends** — resume flagship |

### Optimization Strategies

1. **Schedule heavy tasks off-peak** — run GLM-5.1 agentic sessions before 11:00 or after 15:00 (Brasilia time)
2. **Batch similar tasks** — group related changes into one session instead of multiple small prompts
3. **Use GLM-4.7 as default** — it costs 1× always and handles 90% of coding work
4. **Disable auto-accept for exploration** — avoid wasting 15-20 invocations on uncertain paths
5. **Monitor your quota** at [Usage Statistics](https://z.ai/manage-apikey/subscription)

---

## 3. MCP Tools

### Vision MCP Server (Local)

Provides visual understanding via GLM-4.6V. Shares the 5-hour prompt pool.

**Tools available:**

| Tool | Use Case |
|------|----------|
| `ui_to_artifact` | Convert UI screenshots into code, specs, or prompts |
| `extract_text_from_screenshot` | OCR for code, terminals, docs |
| `diagnose_error_screenshot` | Analyze error snapshots and propose fixes |
| `understand_technical_diagram` | Architecture, flow, UML, ER diagrams |
| `analyze_data_visualization` | Read charts and dashboards |
| `ui_diff_check` | Compare two UI shots for visual drift |
| `image_analysis` | General-purpose image understanding |
| `video_analysis` | Video scene description (≤8MB, MP4/MOV/M4V) |

**Best practices:**
- Place images in local directory and reference by path (don't paste directly — client may bypass MCP)
- Use for debugging UI issues, understanding design mockups, analyzing error screenshots
- Remember: vision uses the same 5-hour pool as your model calls — don't waste on trivial images

**Installation (OpenCode):**
```json
{
    "mcp": {
        "zai-mcp-server": {
            "type": "local",
            "command": ["npx", "-y", "@z_ai/mcp-server"],
            "environment": {
                "Z_AI_API_KEY": "your_api_key",
                "Z_AI_MODE": "ZAI"
            }
        }
    }
}
```

### Web Search MCP Server (Remote)

Real-time web search capability. Remote HTTP service — no local install.

**Tool:** `webSearchPrime` — returns page titles, URLs, summaries, site names, icons.

**Best use cases:**
- Finding latest API documentation or breaking changes
- Researching best practices and patterns
- Checking library compatibility and version info
- Looking up error messages and community solutions

**Installation (OpenCode):**
```json
{
    "mcp": {
        "web-search-prime": {
            "type": "remote",
            "url": "https://api.z.ai/api/mcp/web_search_prime/mcp",
            "headers": {
                "Authorization": "Bearer your_api_key"
            }
        }
    }
}
```

### Web Reader MCP Server (Remote)

Full webpage content extraction. Remote HTTP service.

**Tool:** `webReader` — fetches page title, main content, metadata, links.

**Best use cases:**
- Reading API documentation pages end-to-end
- Parsing open source project READMEs and guides
- Extracting steps from tutorials and blog posts
- Bug resolution using reference documentation
- Building structured knowledge from web content

**Installation (OpenCode):**
```json
{
    "mcp": {
        "web-reader": {
            "type": "remote",
            "url": "https://api.z.ai/api/mcp/web_reader/mcp",
            "headers": {
                "Authorization": "Bearer your_api_key"
            }
        }
    }
}
```

### Zread MCP Server (Remote)

Open source repository Q&A — documentation, code structure, and file content access.

**Tools:**

| Tool | Use Case |
|------|----------|
| `search_doc` | Search docs, code, comments, issues, PRs in GitHub repos |
| `get_repo_structure` | Get directory structure and file list |
| `read_file` | Read complete code content of specific files |

**Best use cases:**
- Quick onboarding with new open source libraries
- Investigating library internals and implementation details
- Checking issue history before filing bugs
- Evaluating dependencies before adopting them

**Installation (OpenCode):**
```json
{
    "mcp": {
        "zread": {
            "type": "remote",
            "url": "https://api.z.ai/api/mcp/zread/mcp",
            "headers": {
                "Authorization": "Bearer your_api_key"
            }
        }
    }
}
```

### MCP Quota Strategy

Web Search + Web Reader + Zread share a **monthly pool**. Vision shares the **5-hour model prompt pool**.

**Optimization:**
- Use `search_doc` (Zread) over `webSearchPrime` + `webReader` combo when researching open source repos — one tool call vs two
- Use `webReader` for specific known URLs instead of `webSearchPrime` when you already know the documentation page
- Reserve Vision MCP for high-value analysis (error screenshots, architecture diagrams) — not casual image queries

---

## 4. Model Mapping (Claude Code Slot Configuration)

Default slot mapping:

| Claude Code Slot | Default Model | Override Recommendation |
|-----------------|---------------|------------------------|
| `ANTHROPIC_DEFAULT_OPUS_MODEL` | GLM-4.7 | GLM-5.1 (for complex tasks) |
| `ANTHROPIC_DEFAULT_SONNET_MODEL` | GLM-4.7 | Keep as-is — sweet spot |
| `ANTHROPIC_DEFAULT_HAIKU_MODEL` | GLM-4.5-Air | Keep as-is — fast & cheap |

**To override**, edit `~/.claude/settings.json`:
```json
{
  "env": {
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "glm-5.1"
  }
}
```

---

## 5. LiteLLM Proxy Access

All 4 GLM models are available through the local LiteLLM proxy, enabling unified logging, budget caps,
and the same access pattern as other providers.

### Architecture

```
opencode → LiteLLM :4000 → z.ai Coding Plan API (api.z.ai/api/coding/paas/v4)
```

### Model Names (via proxy)

| Proxy model_name | Actual model | Context |
|-----------------|-------------|---------|
| `zai/glm-5.1` | glm-5.1 | 200K |
| `zai/glm-5-turbo` | glm-5-turbo | 200K |
| `zai/glm-4.7` | glm-4.7 | 128K |
| `zai/glm-4.5-air` | glm-4.5-air | 128K |

### Configuration

In `litellm/config.yaml`, each model uses `openai/` prefix with explicit `api_base` to the Coding Plan
endpoint (workaround for LiteLLM bug #25479 — native `zai/` provider routes to the wrong endpoint):

```yaml
- model_name: zai/glm-5.1
  litellm_params:
    model: openai/glm-5.1
    api_base: https://api.z.ai/api/coding/paas/v4
    api_key: os.environ/ZAI_API_KEY
```

### API Key Setup

1. Generate a key at https://z.ai/manage-apikey/apikey-list
2. Add to `litellm/.env`: `ZAI_API_KEY=your_key_here`
3. Restart proxy: `oc litellm down && oc litellm up`

### Caveat

z.ai docs state the Coding Plan is "strictly limited to use within officially supported tools".
LiteLLM proxy is technically a third-party intermediary. Monitor for potential restrictions.

---

## 6. Supported Coding Tools

| Tool | Type | Notes |
|------|------|-------|
| Claude Code | CLI / IDE | Full support, slot mapping |
| OpenCode | CLI | Native Z.AI integration, `/models` command |
| Cline | VS Code Extension | Full MCP support |
| Roo Code | VS Code Extension | Full MCP support |
| Kilo Code | VS Code Extension | Full MCP support |
| OpenClaw | CLI | Full support |
| Crush | CLI | Full MCP support |
| Goose | CLI | MCP support (some limitations) |

**Important:** Subscription is strictly limited to supported tools. SDK-based access or unsupported third-party integrations may trigger restrictions.

---

## 7. Concurrency & Multi-Project

- Recommended: **1-2 projects simultaneously**
- Off-peak hours get dynamically increased concurrency limits
- Use subagent patterns within a single project for parallel model calls
- Avoid running multiple heavy GLM-5.1 sessions concurrently during peak hours

---

## 8. GLM-5.1 Advanced Capabilities

When using GLM-5.1, leverage these built-in capabilities:

| Capability | How to Activate |
|-----------|-----------------|
| **Thinking Mode** | `thinking: { "type": "enabled" }` in API calls |
| **Function Calling** | Supported natively — use for tool integration |
| **Context Caching** | Automatic for long conversations |
| **Structured Output** | JSON mode supported |
| **Streaming** | `stream: true` for real-time output |

### Thinking Mode

Enables the model to reason before responding. Recommended for:
- Complex debugging requiring step-by-step analysis
- Architecture decisions with tradeoff evaluation
- Multi-file refactoring planning

```json
{
    "thinking": { "type": "enabled" },
    "max_tokens": 4096,
    "temperature": 1.0
}
```

---

## 9. Quick Reference Card

```
ROUTINE TASKS         → GLM-4.7 (1× always)
COMPLEX TASKS         → GLM-5.1 off-peak (1× promo) or GLM-4.7 peak
TRIVIAL EDITS         → GLM-4.5-Air (Haiku slot, fastest)
PROXY MODELS          → zai/glm-5.1, zai/glm-5-turbo, zai/glm-4.7, zai/glm-4.5-air
RESEARCH OSS LIBS     → Zread MCP (search_doc)
READ KNOWN DOCS       → Web Reader MCP (webReader)
FIND UNKNOWN INFO     → Web Search MCP (webSearchPrime)
DEBUG SCREENSHOTS     → Vision MCP (diagnose_error_screenshot)
UI → CODE             → Vision MCP (ui_to_artifact)
ARCHITECTURE DIAGS    → Vision MCP (understand_technical_diagram)
MONITOR QUOTA         → z.ai/manage-apikey/subscription
AVOID PEAK            → 14:00-18:00 UTC+8
LITELLM UI            → localhost:4000/ui (login: LITELLM_MASTER_KEY)
```

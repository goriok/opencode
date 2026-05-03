# 0008 — LiteLLM Local Proxy

- **Status**: Accepted
- **Data**: 2026-05-03

## Contexto

O setup opera com três fontes de modelos AI sem observabilidade centralizada:
- **Claude Code** → chama `api.anthropic.com` via OAuth (Claude Max subscription)
- **opencode** → chama opencode-go via plugin `oh-my-openagent`
- **z.ai** → GLM Coding Plan via API key (pay-per-subscription, não OAuth)

Sem proxy: sem logging local de custo, sem budget caps, sem visibilidade unificada.

## Decisão

Configurar **LiteLLM** como proxy local único (`localhost:4000`) via Docker Compose com Postgres.

### Arquitetura

```
Claude Code  ─── ANTHROPIC_BASE_URL=http://localhost:4000
             ─── x-litellm-api-key: Bearer <virtual-key>    ──► LiteLLM :4000 ──► Anthropic (OAuth Max)
                                                                               ──► opencode-go API
                                                                               ──► z.ai Coding Plan API

opencode     ─── provider litellm (baseURL localhost:4000/v1) ──► LiteLLM :4000 ──► opencode-go API
             ─── provider litellm (baseURL localhost:4000/v1) ──► LiteLLM :4000 ──► z.ai (glm-5.1, glm-5-turbo, glm-4.7, glm-4.5-air)
```

### Mecanismo de autenticação Anthropic

O LiteLLM usa `forward_client_headers_to_llm_api: true` — repassa o OAuth token do Claude Max
diretamente para a Anthropic API via header `Authorization`. Não requer `ANTHROPIC_API_KEY`.

Os modelos Anthropic no `config.yaml` **não têm `api_key`** — a auth vem inteiramente do header
repassado pelo Claude Code.

### Componentes

| Arquivo | Função |
|---------|--------|
| `litellm/docker-compose.yml` | LiteLLM + Postgres 16, resource limits, healthchecks |
| `litellm/config.yaml` | 15 modelos: Anthropic (3) + opencode-go (8) + z.ai (4) |
| `litellm/.env` | API keys reais (não versionado) |
| `litellm/.env.example` | Template documentado |
| `litellm/setup-litellm.sh` | Script de setup para nova máquina |
| `opencode.jsonc` bloco `"provider"` | Provider `litellm` com `baseURL: localhost:4000/v1` |
| `Taskfile.yml` tasks `litellm:*` | `up`, `down`, `logs`, `status`, `models`, `setup` |
| `~/.claude/settings.json` `"env"` | `ANTHROPIC_BASE_URL` + `ANTHROPIC_CUSTOM_HEADERS` |

### Configuração Claude Code (`~/.claude/settings.json`)

```json
"env": {
  "ANTHROPIC_BASE_URL": "http://localhost:4000",
  "ANTHROPIC_CUSTOM_HEADERS": "x-litellm-api-key: Bearer <virtual-key>"
}
```

A virtual key é gerada via `POST /key/generate` e rastreia spend no UI (`localhost:4000/ui`).

### z.ai — via proxy (Coding Plan API key)

A z.ai coding subscription usa **API key estática** obtida em https://z.ai/manage-apikey/apikey-list,
armazenada como `ZAI_API_KEY` no `.env`. O tráfego passa pelo proxy LiteLLM, permitindo logging e
budget caps no UI.

**Endpoint**: `https://api.z.ai/api/coding/paas/v4` (Coding Plan — NÃO o endpoint geral `/api/paas/v4`).

**Bug workaround**: O provider nativo `zai/` do LiteLLM roteia para o endpoint geral, causando 429s
com Coding Plan. Solução: usar `openai/` prefix + `api_base` manual no `config.yaml`.
Ref: https://github.com/BerriAI/litellm/issues/25479

**Modelos disponíveis**: `glm-5.1`, `glm-5-turbo`, `glm-4.7`, `glm-4.5-air`

**Caveat**: z.ai docs dizem que a subscription é "strictly limited to use within officially supported
tools". LiteLLM proxy é tecnicamente um intermediário third-party.

### Correção de 429s

Dois mecanismos de retry independentes no LiteLLM precisam ser zerados:

1. **Router-level** (`litellm_settings.num_retries: 0`) — controla `router.py:async_function_with_retries`
2. **HTTP-level** (`litellm_params.max_retries: 0` por modelo) — controla `_async_post_anthropic_messages_with_http_error_retry` no httpx handler

Com `num_retries: 2` (padrão router) + `max_retries` não zerado, cada request com 429 podia gerar 3+ chamadas totais. Ambos precisam ser `0` para Claude Max (OAuth com rate limits por minuto).

## Alternativas Consideradas

1. **Sem proxy** — status quo. Zero observabilidade local, sem budget caps.
2. **ccproxy / claude-code-router** — só Claude Code, sem suporte a opencode-go.
3. **LiteLLM sem Postgres** — sem UI funcional; `store_model_in_db: false` quebra o login.

## Consequências

**Positivas:**
- Logging unificado no UI (`localhost:4000/ui`) com spend por virtual key
- Budget caps configuráveis por key via `POST /key/generate`
- `task litellm:up/down/logs/status/models` para operação diária
- Claude Code Max sem API key paga — usa OAuth subscription

**Negativas:**
- Proxy offline = Claude Code falha (está configurado em `settings.json`)
- Requer Docker em execução
- Latência adicional ~1-5ms por chamada

**Riscos:**
- Endpoint opencode-go (`https://opencode.ai/zen/go/v1`) pode mudar — monitorar
- Virtual key expira se o Postgres for apagado — regenerar com `setup-litellm.sh --claude-code`

## Setup em nova máquina

```bash
bash ~/.config/opencode/litellm/setup-litellm.sh
# opencode → /connect zai-coding-plan
```

Ver [RB-008](../runbooks/rb-008-litellm-proxy-setup.md) para passos detalhados.

## Relacionados

- [0006 — Cache Optimization](./0006-cache-optimization-opencode.md)
- [0007 — OpenCode Go Model Strategy](./0007-opencode-go-model-strategy.md)
- [RB-008 — LiteLLM Proxy Setup](../runbooks/rb-008-litellm-proxy-setup.md)

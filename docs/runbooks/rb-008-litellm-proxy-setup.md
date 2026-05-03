# RB-008 — Setup LiteLLM Proxy (Claude Code + opencode)

**Quando usar**: Configurar o proxy LiteLLM local em uma máquina nova.  
**Tempo estimado**: 5-10 minutos  
**Pré-requisitos**: Docker instalado, repo `~/.config/opencode` clonado, Claude Code instalado

## Contexto

```
Claude Code  ──► LiteLLM :4000 ──► Anthropic API (OAuth Max — sem API key paga)
opencode     ──► LiteLLM :4000 ──► opencode-go API
opencode     ──► LiteLLM :4000 ──► z.ai Coding Plan (glm-5.1, glm-5-turbo, glm-4.7, glm-4.5-air)
```

**UI de monitoramento**: `http://localhost:4000/ui` (login: valor de `LITELLM_MASTER_KEY`)

**GitHub Copilot**: 18 modelos preparados no `config.yaml` (OpenAI, Claude, Gemini, Codex) mas
comentados — OAuth device flow crasha o proxy na inicialização. Para ativar, veja instruções no `config.yaml`.

---

## Setup automático (nova máquina)

```bash
bash ~/.config/opencode/litellm/setup-litellm.sh
```

O script faz tudo: cria `.env`, sobe o proxy, gera virtual key e configura `~/.claude/settings.json`.

---

## Setup manual (passo a passo)

### 1. Verificar pré-requisitos

```bash
docker --version          # Docker 24+
docker compose version    # Compose v2+
```

### 2. Criar `.env` com as API keys

```bash
cp ~/.config/opencode/litellm/.env.example ~/.config/opencode/litellm/.env
# edite o arquivo:
nano ~/.config/opencode/litellm/.env
```

| Variável | Valor |
|----------|-------|
| `LITELLM_MASTER_KEY` | `sk-litellm-local` (ou string segura à sua escolha) |
| `OPENCODE_GO_API_KEY` | Copie de `https://opencode.ai/auth` → "API Key" |
| `ANTHROPIC_API_KEY` | **Deixe vazio** — Claude Code usa OAuth Max, não API key |
| `ZAI_API_KEY` | Copie de `https://z.ai/manage-apikey/apikey-list` |

> **z.ai endpoint**: O config.yaml aponta para `https://api.z.ai/api/coding/paas/v4` (Coding Plan).
> O provider nativo `zai/` do LiteLLM roteia pro endpoint errado — por isso usamos `openai/` prefix.
> Ref: https://github.com/BerriAI/litellm/issues/25479

### 3. Subir o proxy

```bash
cd ~/.config/opencode && task litellm:up
```

Aguarde ~20s para migrations do Postgres rodarem.

### 4. Verificar

```bash
task litellm:status    # "I'm alive!"
task litellm:models    # lista 15 modelos (3 Anthropic + 8 opencode-go + 4 z.ai)
```

### 5. Configurar Claude Code

```bash
bash ~/.config/opencode/litellm/setup-litellm.sh --claude-code
```

Ou manualmente — gere a virtual key:

```bash
source ~/.config/opencode/litellm/.env
curl -s -X POST http://localhost:4000/key/generate \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"key_alias":"claude-code-max","models":["claude-sonnet-4-6","claude-opus-4-7","claude-haiku-4-5-20251001"]}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['key'])"
```

Adicione ao `~/.claude/settings.json`:

```json
"env": {
  "ANTHROPIC_BASE_URL": "http://localhost:4000",
  "ANTHROPIC_CUSTOM_HEADERS": "x-litellm-api-key: Bearer <virtual-key-gerada>"
}
```

### 6. Testar Claude Code via proxy

```bash
claude -p "ping"
# deve retornar: pong

task litellm:logs
# deve mostrar: POST /v1/messages?beta=true 200 OK
```

### 7. Verificar z.ai via proxy

```bash
# Testar chamada direta ao endpoint de Coding Plan
source ~/.config/opencode/litellm/.env
curl -s https://api.z.ai/api/coding/paas/v4/chat/completions \
  -H "Authorization: Bearer $ZAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"glm-4.5-air","messages":[{"role":"user","content":"reply pong"}],"max_tokens":50}' \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('choices',[{}])[0].get('message',{}).get('content','(empty)'))"
```

Deve retornar `pong` ou similar.

> **Nota**: z.ai docs recomendam usar Coding Plan apenas em ferramentas oficialmente suportadas.
> LiteLLM proxy é tecnicamente um intermediário third-party.

### 8. Usar opencode via proxy

O `opencode.jsonc` já tem o provider `litellm` configurado com `apiKey: "sk-litellm-local"`.

No opencode, use `/models` e selecione modelos do grupo `LiteLLM Local Proxy`:
- `litellm/opencode-go/deepseek-v4-flash`
- `litellm/opencode-go/deepseek-v4-pro`
- etc.

---

## Operação diária

```bash
task litellm:up      # inicia (se não estiver rodando)
task litellm:down    # para
task litellm:logs    # monitora chamadas em tempo real
task litellm:status  # health check rápido
task litellm:models  # lista modelos disponíveis
```

O container tem `restart: unless-stopped` — reinicia automaticamente com o Docker.

---

## Validação completa

- [ ] `task litellm:status` retorna `"I'm alive!"`
- [ ] `task litellm:models` lista 15 modelos (3 Anthropic + 8 opencode-go + 4 z.ai)
- [ ] `claude -p "ping"` retorna `pong`
- [ ] `task litellm:logs` mostra `POST /v1/messages 200 OK`
- [ ] `http://localhost:4000/ui` abre; virtual key `claude-code-max` aparece com `Last Active` atualizado
- [ ] z.ai models respondem via proxy (`zai/glm-4.5-air` retorna 200 OK)

---

## Troubleshooting

**Claude Code com 429 (rate limit)**
- Normal com Claude Max — o proxy tem dois níveis de retry, ambos zerados:
  - `litellm_settings.num_retries: 0` (router-level)
  - `max_retries: 0` em cada modelo Anthropic (HTTP-level, `_async_post_anthropic_messages_with_http_error_retry`)
- Se 429 aparecer repetidamente, verifique se o `config.yaml` tem ambos os zeros
- Aguarde o rate limit da Anthropic resetar (janela de 1 min)

**Claude Code com erro de autenticação após restart**
- Virtual key foi perdida (Postgres apagado?) — regenere:
  ```bash
  bash ~/.config/opencode/litellm/setup-litellm.sh --claude-code
  ```
- Atualize `ANTHROPIC_CUSTOM_HEADERS` em `~/.claude/settings.json`

**Proxy não sobe**
```bash
task litellm:logs          # ver erro de startup
docker compose ps          # verificar containers
```

**opencode-go com 401**
- API key expirou — renove em `opencode.ai/auth`
- Atualize `OPENCODE_GO_API_KEY` em `~/.config/opencode/litellm/.env`
- Reinicie: `task litellm:down && task litellm:up`

**UI não aceita login**
- Use o valor exato de `LITELLM_MASTER_KEY` do `.env` (não a virtual key)
- Verifique: `grep LITELLM_MASTER_KEY ~/.config/opencode/litellm/.env`

---

## Relacionados

- [RB-001 — Setup de Máquina Nova](./rb-001-setup-maquina-nova.md)
- [MADR 0008 — LiteLLM Proxy](../madr/0008-litellm-proxy.md)
- `~/.config/opencode/litellm/` — todos os arquivos de configuração

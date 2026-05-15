---
name: autonomous-agent
description: Cria um novo agent autônomo Python do zero ou adiciona tools a um agent existente, seguindo o padrão estabelecido no mcx-companion. Cobre estrutura do projeto, servidor Starlette + MCP, loop ReAct, integração com companions, e manifests Kubernetes. Ao finalizar, sugere /concept para documentar conceitos novos introduzidos. Ativar quando o usuário pedir para criar um agent, adicionar tools a um agent, ou construir um bot autônomo.
argument-hint: <nome-do-agent> | add-tool <agent-path> <tool-name>
allowed-tools: Read, Write, Bash, Glob
tool: claude-only
---

# Autonomous Agent — Criar ou Evoluir um Agent Autônomo

## Quando Ativar

- "cria um agent para X"
- "quero um bot que monitora Y"
- "adiciona uma tool Z no agent"
- "novo agent integrado com companions"

## Modo de operação

Determinar o modo pelo argumento ou pela intenção:

| Modo | Trigger | O que faz |
|------|---------|-----------|
| **create** | nome novo (ex: `git-companion`) | Cria o projeto completo do zero |
| **add-tool** | `add-tool <path> <tool-name>` | Adiciona tool ao `mcp_server.py` de um agent existente |

---

## MODO: Criar Agent do Zero

### 1. Coletar contexto

Antes de criar qualquer arquivo, confirmar com o usuário:
- **Nome do agent** — formato `kebab-case` (ex: `git-companion`)
- **Responsabilidade** — o que o agent observa/executa
- **Triggers** — CronJob? Webhook do companions? Alertmanager?
- **Tools read-only** — o que o agent pode fazer autonomamente
- **Tools mutantes** — o que exige aprovação humana (HITL via companions)
- **Namespace K8s** — padrão: mesmo nome do agent

Se o usuário não especificar, usar defaults do padrão mcx-companion.

### 2. Estrutura de arquivos a criar

```
~/sources/<agent-name>/
├── pyproject.toml
├── Dockerfile
└── src/<agent_name>/          # underscores no módulo Python
    ├── __init__.py
    ├── cli.py                 # entrypoints: serve, digest, react
    ├── config.py              # Config class com env vars
    ├── agent.py               # ReAct loop + MCP in-process
    ├── companions.py          # post_message, create_pending_action
    ├── memory.py              # mem0 + fastembed + Qdrant
    ├── mcp_server.py          # FastMCP com @mcp.tool()
    ├── server.py              # Starlette + uvicorn + ThreadPoolExecutor
    ├── tools/
    │   ├── __init__.py
    │   └── <domain>.py        # funções Python das tools
    └── triggers/
        ├── __init__.py
        ├── chat.py            # handle() + fetch_history()
        ├── cron.py            # main() — digest diário
        └── webhook.py         # main() — reação a alertas
```

E em `~/sources/my-cluster/k8s/apps/<agent-name>/`:
```
├── kustomization.yaml
├── namespace.yaml
├── rbac.yaml
├── deployment.yaml
├── service.yaml
├── ingress.yaml
└── cronjob-digest.yaml        # se tiver trigger cron
```

### 3. Gerar os arquivos

Usar os templates em `templates/` como base. Substituir `$AGENT_NAME`, `$AGENT_MODULE`, `$DESCRIPTION`, etc.

**Ordem de criação:**
1. `pyproject.toml` — deps base (copiar de mcx-companion, ajustar nome)
2. `config.py` — env vars obrigatórias: `LITELLM_API_KEY`, `COMPANIONS_URL`, `COMPANIONS_AGENT_KEY`
3. `tools/<domain>.py` — funções Python das tools (o núcleo da lógica)
4. `mcp_server.py` — FastMCP registrando as tools com `@mcp.tool()`
5. `agent.py` — ReAct loop usando `mcp._tool_manager` + `mcp.call_tool()`
6. `memory.py` — mem0 config com fastembed + Qdrant
7. `companions.py` — `post_message()` e `create_pending_action()`
8. `triggers/chat.py` — `handle()` + `fetch_history()`
9. `triggers/cron.py` — `main()` do digest
10. `triggers/webhook.py` — `main()` de reação
11. `server.py` — Starlette + ThreadPoolExecutor + SSE MCP
12. `cli.py` — Typer com subcomandos `serve`, `digest`, `react`
13. `Dockerfile` — python:3.12-slim + uv pip install
14. Manifests K8s

### 4. Registrar no mcx.toml

Adicionar bloco em `~/sources/my-cluster/mcx.toml`:

```toml
[[apps]]
name = "<agent-name>"
source_path = "../<agent-name>"
kustomize_path = "k8s/apps/<agent-name>"
rsync_excludes = [".git/", ".venv/", "__pycache__/", "*.pyc", ".env*"]
```

### 5. Registrar no companions

Instruir o usuário a criar o agent no companions:
```
GET https://companions.goriok.com/admin/agents
→ criar agent "<agent-name>" e copiar a API key gerada
```

Depois criar o secret K8s:
```bash
kubectl create secret generic <agent-name>-secret \
  --namespace <agent-name> \
  --from-literal=LITELLM_API_KEY=<virtual-key> \
  --from-literal=COMPANIONS_URL=https://companions.goriok.com \
  --from-literal=COMPANIONS_AGENT_KEY=<key-do-companions>
```

### 6. Deploy inicial

```bash
cd ~/sources/my-cluster
mcx deploy image <agent-name>
kubectl apply -k k8s/apps/<agent-name>/
kubectl rollout status deployment/<agent-name> -n <agent-name>
```

### 7. Verificação

- `curl https://<agent-name>.goriok.com/health` → `{"status": "ok"}`
- Mandar mensagem no companions → resposta do agent no canal
- `kubectl logs -n <agent-name> -l app=<agent-name>` → ver `[chat] done`

---

## MODO: Adicionar Tool a Agent Existente

### 1. Ler o mcp_server.py atual

Identificar tools existentes e o padrão de nomenclatura.

### 2. Criar a função Python em tools/

```python
# tools/<domain>.py
def <tool_name>(<params>) -> str:
    """Descrição clara do que a tool faz."""
    ...
    return resultado_como_string
```

### 3. Registrar no mcp_server.py

```python
from .tools.<domain> import <tool_name>

@mcp.tool()
def <tool_name>(<params>) -> str:
    """Docstring usada como description no MCP — seja descritivo.

    Args:
        <param>: Descrição do parâmetro.
    """
    return <tool_name>(<params>)
```

O `agent.py` detecta automaticamente — não precisa editar `TOOLS` ou `TOOL_HANDLERS`.

### 4. Rebuild e deploy

```bash
cd ~/sources/my-cluster
mcx deploy image <agent-name>
kubectl rollout restart deployment/<agent-name> -n <agent-name>
```

### 5. Verificar no LiteLLM

```bash
curl https://litellm.goriok.com/v1/mcp/tools \
  -H "Authorization: Bearer <master-key>" | jq '.tools[].name'
```

A nova tool deve aparecer prefixada com `<agent_name>-<tool_name>`.

---

## Padrões arquiteturais obrigatórios

### Fire-and-forget no webhook
O handler HTTP **sempre** responde 200 antes de processar:
```python
async def webhook_chat(request: Request) -> JSONResponse:
    body = await request.json()
    loop = asyncio.get_running_loop()
    loop.run_in_executor(_executor, _chat_task, channel, message)
    return JSONResponse({"ok": True})  # responde imediatamente
```

### asyncio em thread worker
Nunca usar `asyncio.run()` dentro de thread do executor — criar loop explícito:
```python
loop = asyncio.new_event_loop()
try:
    return loop.run_until_complete(_run())
finally:
    loop.close()
```

### MCP in-process
O agent usa `mcp.call_tool()` diretamente — sem conexão SSE de rede para si mesmo:
```python
result = await mcp.call_tool(name, arguments)  # in-process
```
O endpoint SSE `/mcp/sse` existe para clientes externos (Claude Code, LiteLLM).

### mem0 API atual
```python
# search usa filters, não user_id direto
memory.search(query, filters={"user_id": user_id}, limit=5)
# add ainda usa user_id
memory.add(messages, user_id=user_id)
```

### Tools mutantes → HITL
Tools que modificam estado do cluster não executam diretamente:
```python
@mcp.tool()
def deploy_app(app_name: str) -> str:
    """Faz deploy de uma aplicação. Requer aprovação humana."""
    action_id = create_pending_action(
        command=f"mcx deploy cluster --app {app_name}",
        description=f"Deploy de {app_name}",
        channel="cluster",
    )
    return f"Ação pendente criada: {action_id}. Aguardando aprovação."
```

---

## Ao finalizar

Sempre sugerir ao usuário documentar os conceitos novos introduzidos:

```
Quer documentar algum conceito novo que usamos aqui?
Exemplos:
  /concept <conceito-implementado>
  /concept <padrão-novo-descoberto>
```

---

## Anti-patterns

- ❌ Criar `TOOL_HANDLERS` dict manual — o `mcp_server.py` + `agent.py` gerenciam isso
- ❌ Chamar `asyncio.run()` dentro de thread do `ThreadPoolExecutor`
- ❌ Handler Starlette sem retornar `JSONResponse` (causa `NoneType` error)
- ❌ Tools mutantes executando sem criar `PendingAction` no companions
- ❌ Usar `provider: huggingface` no mem0 — requer `sentence_transformers` não instalado; usar `fastembed`
- ❌ Esquecer de fechar o event loop criado na thread (`loop.close()`)
- ❌ Secret K8s com nome diferente do padrão `<agent-name>-secret`
- ❌ Registrar o agent no mcx.toml sem adicionar ao `k8s/apps/kustomization.yaml`

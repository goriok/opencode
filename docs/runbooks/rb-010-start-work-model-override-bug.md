# RB-010 — /start-work: Model Overrides Not Applied

**Status:** Known Bug (upstream)
**Affects:** oh-my-openagent ≥ 3.x (confirmed: 3.17.5 e 4.0.0)
**Severity:** Medium — modelo errado consome créditos do provider errado

---

## Sintoma

Ao executar `/start-work`, os agentes `sisyphus` e `atlas` são iniciados com o modelo padrão
do plugin (ex: `anthropic/claude-opus-4-7`, `anthropic/claude-sonnet-4-6`) ao invés dos modelos
configurados no `oh-my-openagent.jsonc` (ex: `zai/glm-4.7`).

---

## Root Cause

### Onde o problema está

`src/hooks/start-work/start-work-hook.ts` — função `createStartWorkHook`:

```js
const activeAgent = isAgentRegistered("atlas") ? "atlas" : "sisyphus";
updateSessionAgent(input.sessionID, activeAgent);
if (output.message) {
  output.message["agent"] = resolveRegisteredAgentName(activeAgent) ?? activeAgent;
  // ← output.message["model"] NUNCA é setado aqui
}
```

O hook troca o agente mid-session mas **não injeta o modelo** correspondente.

### Por que o config é ignorado

O fluxo correto de aplicação de model override é:

```
chat.message recebido
  → getStoredMainSessionModel()
      → se hasExplicitAgentModelOverride(agent) → retorna undefined (pula)
      → se não → retorna getSessionModel() (model anterior da sessão)
  → modelFallback hook
      → só age quando há fallback PENDENTE (erro 429/503 etc.)
      → não aplica proativamente
```

`hasExplicitAgentModelOverride` retorna `true` quando o agente tem `model` em `pluginConfig.agents`,
mas isso faz o runtime **pular** a aplicação do session model — não aplicar o override.
O override de agente só é aplicado no **início da sessão** via `createBuiltinAgents()`, não quando
o hook troca o agente mid-session.

### Confirmação: v4.0.0 tem o mesmo bug

```
Versão instalada:  3.17.5
Versão mais nova:  4.0.0
Bug no start-work: PRESENTE em ambas (código idêntico)
```

O hook `start-work` não foi alterado entre 3.x e 4.0.0.

---

## Impacto

| Cenário | Comportamento Real | Comportamento Esperado |
|---------|-------------------|----------------------|
| `/start-work` sem atlas registrado | `sisyphus` com `anthropic/claude-opus-4-7` | `sisyphus` com `zai/glm-4.7` |
| `/start-work` com atlas registrado | `atlas` com `anthropic/claude-sonnet-4-6` | `atlas` com modelo configurado |
| Subagentes chamados via `call_omo_agent` | Correto (usa `resolveModelAndFallbackChain`) | — |

Subagentes **não são afetados** — eles passam por `resolveModelAndFallbackChain` que lê o
`pluginConfig.agents` corretamente.

---

## Workarounds

### Workaround 1 — Selecionar o modelo manualmente (mais eficaz)

Após executar `/start-work`, trocar manualmente o modelo na UI do opencode para o modelo desejado
antes da primeira mensagem ser processada.

### Workaround 2 — Project-level config (parcialmente eficaz)

O `loadPluginConfig` faz merge de:
1. `~/.config/opencode/oh-my-openagent.jsonc` (user config)
2. `<project>/.opencode/oh-my-openagent.jsonc` (project config)

O project config é aplicado por último e sobrescreve o user config para `agents` e `categories`.
**Isso não resolve** o bug de mid-session agent switch, mas garante que o config está correto
para o carregamento inicial de sessões novas no projeto.

Para aplicar em um projeto:

```bash
mkdir -p <projeto>/.opencode
cp ~/.config/opencode/oh-my-openagent.jsonc <projeto>/.opencode/oh-my-openagent.jsonc
```

O conteúdo pode ser mínimo — só os campos que diferem do user config:

```jsonc
// <projeto>/.opencode/oh-my-openagent.jsonc
{
  "agents": {
    "sisyphus": { "model": "zai/glm-4.7" },
    "atlas":    { "model": "zai/glm-4.7" }
  }
}
```

### Workaround 3 — Atualizar para v4.0.0 (não resolve)

Bug confirmado presente na v4.0.0. Não há benefício em atualizar para esse bug específico.

---

## Fix Upstream Necessário

O `start-work-hook.ts` precisa injetar `output.message["model"]` após setar o agente:

```ts
// Após: output.message["agent"] = resolveRegisteredAgentName(activeAgent) ?? activeAgent;
const agentConfigKey = getAgentConfigKey(activeAgent);
const agentModelOverride = pluginConfig.agents?.[agentConfigKey]?.model;
if (agentModelOverride) {
  const parsed = parseModelString(agentModelOverride);
  if (parsed) {
    output.message["model"] = { providerID: parsed.providerID, modelID: parsed.modelID };
    if (parsed.variant) output.message["variant"] = parsed.variant;
  }
}
```

Reportar em: https://github.com/code-yeongyu/oh-my-openagent/issues

---

## Referências de código

| Arquivo (dist/index.js) | Linha (v3.17.5) | Linha (v4.0.0) |
|-------------------------|-----------------|-----------------|
| `createStartWorkHook` | 85226 | 89528 |
| `hasExplicitAgentModelOverride` | 124652 | — |
| `getStoredMainSessionModel` | 124662 | — |
| `createModelFallbackHook` | 71711 | — |
| `AGENT_MODEL_REQUIREMENTS` | 18710 | 7426 |
| `resolveModelAndFallbackChain` | 97080 | — |

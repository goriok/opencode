# 0006 — Cache Optimization for Opencode Token Usage

- **Status**: Accepted
- **Data**: 2026-04-30

## Contexto

O setup opencode utiliza o provider `opencode-go` (com modelos como deepseek-v4-pro, kimi-k2.6, glm-5.1) e consome tokens significativos em sessões longas. Antes da otimização, as estatísticas mostravam:

- Cache Read: 764.1M tokens
- Cache Write: 18.1M tokens
- Cache Hit Rate: ~88%

Apesar do cache já estar ativo (via `applyCaching()` automático do opencode), várias otimizações adicionais estavam disponíveis mas não habilitadas:

1. **MCP Lazy Loading** — MCP servers carregam todas as tool definitions no prefix do system prompt, consumindo 32k+ tokens por sessão
2. **Cache Stabilization** — Instruções dinâmicas (data, cache hints) mudam a cada turno, invalidando o cache de prefixo
3. **Cache TTL** — O TTL padrão de 5 minutos causa re-criação frequente em sessões com pausas
4. **Aggressive Truncation** — O plugin oh-my-openagent não truncava agressivamente o contexto antigo

### Limitações do Provider

O provider `opencode-go` usa OpenAI SDK sob o hood, o que impede:

- ❌ `anthropic-beta: token-efficient-tools-2025-02-19` header (compressão de tool schemas em 20-50%)
- ❌ `defer_loading` nativo do Anthropic (lazy loading de tools via API)
- ❌ `cache_control` body params customizados (já injetado automaticamente por `applyCaching()`)

## Decisão

Habilitar três flags experimentais no `opencode.jsonc` e uma mudança no `oh-my-openagent.jsonc`:

### 1. `experimental.mcp_lazy: true` (opencode.jsonc)

Lazy load de MCP tools. Em vez de carregar todas as tool definitions no prefixo do system prompt, o modelo recebe apenas nomes de ferramentas e busca schemas sob demanda. Preserva o cache de prefixo quando novas ferramentas são descobertas.

**Economia estimada**: 32k+ tokens por sessão (50-70k com 5+ MCP servers)

### 2. `experimental.cache_stabilization: true` (opencode.jsonc)

Congela instruções dinâmicas (data atual, hints de cache) para que o prefixo do system prompt permaneça estável entre turnos. Isso maximiza o cache hit rate do prefixo.

**Economia estimada**: Reduz invalidações de cache de prefixo

### 3. `experimental.cache_1h_ttl: true` (opencode.jsonc)

Estende o TTL do cache de 5 minutos para 1 hora. Custo: 2x o preço base de input para cache writes. Benefício: evita re-criação de cache em sessões com pausas entre interações.

**Tradeoff**: Maior custo por cache write, mas menor frequência de re-criação

### 4. `aggressive_truncation: true` (oh-my-openagent.jsonc)

Permite que o plugin trunque contexto antigo de forma mais agressiva quando o contexto está cheio, em vez de preservar todo o histórico.

**Tradeoff**: Pode perder contexto antigo, mas economiza tokens significativos em sessões longas

## Alternativas Consideradas

1. **Token-efficient-tools beta header** — Não suportado pelo provider opencode-go (usa OpenAI SDK, não Anthropic API direta). Seria a otimização de maior impacto (20-50% de economia em tool definitions).
2. **defer_loading nativo (Anthropic)** — Ainda não implementado no opencode (issue #23298). Quando implementado, substituirá `mcp_lazy` com solução nativa.
3. **Manter status quo** — Cache já funciona (88% hit rate), mas sem as otimizações de lazy loading e estabilização.
4. **Desabilitar MCP servers** — Reduziria tokens mas perderia funcionalidade.

## Consequências

**Positivas:**
- Redução estimada de 32k+ tokens por sessão com MCP lazy loading
- Maior cache hit rate com estabilização de prefixo
- Menos re-criações de cache com TTL de 1h
- Contexto mais enxuto com truncation agressivo

**Negativas:**
- `cache_1h_ttl` custa 2x o preço base de input para cache writes
- `aggressive_truncation` pode perder contexto antigo em sessões longas
- `mcp_lazy` pode causar latência extra na primeira chamada de cada ferramenta (busca sob demanda)
- Bug conhecido: primeiro ToolSearch invalida prompt-cache prefix (Issue #53132), recupera-se monotonicamente no turn N+2

**Riscos:**
- As flags são experimentais e podem mudar em versões futuras do opencode
- O bug do ToolSearch (issue #53132) causa invalidação de cache na primeira busca, mas é transitório

## Baseline (pré-otimização)

| Métrica | Valor |
|---------|-------|
| Cache Read | 764.1M tokens |
| Cache Write | 18.1M tokens |
| Cache Hit Rate | ~88% |
| MCP Servers | memory (disabled) |
| Plugins | 5 ativos (dcp, mem, oh-my-openagent, workspace, micode) |

## Referências

- [Anthropic Prompt Caching docs](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching)
- [Token-Efficient Tool Use beta](https://docs.anthropic.com/en/docs/build-with-claude/tool-use-token-efficient)
- [Opencode issue #23298 — defer_loading support](https://github.com/opencodeco/opencode/issues/23298)
- [Claude Code issue #53132 — ToolSearch cache invalidation](https://github.com/anthropics/claude-code/issues/53132)
# 0003 — Plugin Coexistence Strategy

- **Status**: Accepted
- **Data**: 2026-04-18

## Contexto

O setup OpenCode usa múltiplos plugins com funcionalidades sobrepostas: opencode-mem (memória), oh-my-opencode (hooks + agents), opencode-workspace (multi-agent), e DCP (context pruning). Precisávamos de uma estratégia para que funcionem em harmonia sem conflitos.

## Decisão

Adotar uma estratégia de **camadas harmônicas** onde cada plugin tem domínio claro:

| Camada | Plugin | Responsabilidade |
|--------|--------|-----------------|
| Memória | opencode-mem | Persistência vetorial |
| Contexto | DCP | Pruning automático |
| Arsenal | oh-my-opencode | Hooks + agents rápidos |
| Orquestração | workspace | Multi-agent bundle |

Conflitos resolvidos por **prioridade de camada**: quando dois plugins tentam agir no mesmo domínio, a camada mais específica vence.

## Alternativas Consideradas

1. **Plugin único** — Perde especialização. Nenhum plugin faz tudo bem.
2. **Sem coordenação** — Conflitos inevitáveis (ex: memória MCP vs opencode-mem).
3. **Config customizada por projeto** — Muito overhead, difícil de manter.

## Consequências

**Positivas:**
- Cada plugin faz uma coisa bem feita
- Configuração central em `opencode.jsonc`
- Decision tree clara para o usuário

**Negativas:**
- 4 plugins = 4 fontes de configuração
- Debugar interações entre plugins é complexo
- Atualização de um plugin pode quebrar harmonia
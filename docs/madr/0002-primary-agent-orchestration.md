# 0002 — Primary Agent Orchestration

- **Status**: Accepted
- **Data**: 2026-04-20

## Contexto

O ecossistema OpenCode tem 191 agentes instalados do agency-agents, mais agentes customizados. Precisávamos de uma camada orquestradora que delega para especialistas em vez de tentar fazer tudo com um agente genérico.

## Decisão

Adotar três agentes primários orquestradores, cada um com squad de subagentes especializados:

- **Alan Turing** — SDLC completo (requirements → monitoring)
- **Grace Hopper** — Troubleshooting (detection → prevention)
- **Ada Lovelace** — Análise exploratória rápida

Cada primário referencia subagentes do agency-agents por nome, sem duplicar definições.

## Alternativas Consideradas

1. **Agente único master** — Escala mal, contexto excessivo, sem especialização.
2. **Sem orquestração** — Usuário escolhe agente manualmente a cada task. Fadiga de decisão.
3. **Orquestração por framework externo** — Acoplamento desnecessário, complexidade adicional.

## Consequências

**Positivas:**
- Especialização clara — cada orquestrador sabe quando delegar
- Menos fadiga de decisão — usuário escolhe entre 3 perfis, não 191
- Compatível com os frameworks existentes (ISO-25010, ATAM, RM-ODP)
- Subagentes são intercambiáveis — agency-agents pode evoluir independentemente

**Negativas:**
- Overhead de contexto ao invocar orquestrador + subagentes
- Nem sempre claro qual orquestrador usar para tasks híbridas
- Manutenção de 3 arquivos de agente primário
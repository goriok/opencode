# 0009 — Tier-routing contract: agents/skills delegate to `oh-my-openagent.jsonc`

- **Status**: Accepted
- **Data**: 2026-05-08

## Contexto

O sistema de tiers (`oc tier set <name>`) regenera `oh-my-openagent.jsonc` a partir de `tiers/*.yaml`,
mapeando cada agente (sisyphus, oracle, prometheus, …) e cada categoria (writing, deep, ultrabrain, …)
para um modelo concreto por provider. O catálogo `providers/*.yaml` valida elegibilidade.

A questão operacional: se um agente individual em `agents/*.md` ou um skill em `skills/*/SKILL.md`
declarasse `model:` no frontmatter, ele **bypassaria** o mapa central — quebrando orçamento,
elegibilidade e a promessa de "trocar tier = realocar tudo".

Esta MADR documenta o contrato observado e o defende com um guard test.

## Decisão

**O único ponto mutável de roteamento é `oh-my-openagent.jsonc`.** Personas (`agents/*.md`) e
skills (`skills/*/SKILL.md`) **não podem** carregar `model:` no frontmatter. Routing é resolvido
exclusivamente pelo plugin `oh-my-openagent` via o JSONC central.

### Pipeline canônico

```
tiers/<name>.yaml
   └─ render_plugin()         src/ocx/tier_apply.py:65-99
        └─ oh-my-openagent.jsonc          ← ÚNICO arquivo lido pelo plugin em runtime
              └─ plugin oh-my-openagent   carregado por opencode.jsonc:66
```

### Auditoria (2026-05-08)

`grep -rEn "^model:" agents/ skills/` → **0 matches** em 167 agents + 21 skills.

Falsos positivos descartados:
- `agents/carousel-growth-engine.md:46,118` — `gemini-3.1-flash-image-preview` documenta
  subprocesso externo (`generate_image.py`) para gerar imagens, não o LLM que roda o agente.
- `workflows/session-usage-analyzer.py:42` — campo `model: str` em dataclass para parsear
  logs de telemetria, não declarar modelo.

### Defesa contínua

Guard test em `tests/test_agents_no_model_override.py` falha se algum `agents/*.md` ou
`skills/*/SKILL.md` introduzir frontmatter `model:`. Esse é o backstop contra regressão.

## Consequências

**Positivas:**
- `oc tier set <tier>` é suficiente para realocar 100% do roteamento — sem auditoria por agente.
- Catálogo de providers (`providers/*.yaml`) é a única fonte de verdade para elegibilidade e custo.
- Mudanças de modelo são reproduzíveis e revisáveis em PRs sobre `tiers/*.yaml`.

**Negativas:**
- Personas perdem flexibilidade individual de modelo (intencional — é o ponto).
- Adicionar um novo agente exige atualizar `tiers/*.yaml` para todos os tiers ativos
  (validado por `tier_apply.validate_tier`).

## Referências

- `src/ocx/tier_apply.py:44-99` — `render_plugin`, `_build_agent_entry`, `validate_tier`
- `src/ocx/providers.py` — `validate_eligibility`, `cost_label`
- `AGENTS.md` §"Provider catalog"
- MADR 0003 (plugin coexistence), 0007 (opencode-go strategy), 0008 (LiteLLM proxy)

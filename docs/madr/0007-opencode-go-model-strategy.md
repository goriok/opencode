# 0007 — Opencode Go Model Strategy

- **Status**: Accepted
- **Data**: 2026-05-03

## Contexto

A assinatura OpenCode Go ($10/mês) oferece 14 modelos de programação, mas a configuração original em `oh-my-openagent.jsonc` roteava apenas 4 modelos (deepseek-v4-pro, deepseek-v4-flash, glm-5.1, mimo-v2-omni). Os 10 modelos restantes ficavam subutilizados, representando desperdício de capacidade incluída na assinatura.

Além disso, alguns agentes recebiam modelos superdimensionados para sua complexidade:
- `sisyphus` (daily driver) usava `glm-5.1` (4.3K req/mês) — overkill para tarefas persistentes
- `explore` (busca) usava `deepseek-v4-flash` (37.3K req/mês) — quando `qwen3.5-plus` oferece 50.5K req/mês
- Modelos de menor custo (MiniMax, Qwen) não eram usados — desperdício de capacidade econômica

## Decisão

Expandir de 4 para 7 modelos ativos, roteando cada agente para o modelo que maximiza **volume de requests dentro do mesmo orçamento**:

| Modelo | Agentes | Req/mês | Racional |
|--------|---------|---------|----------|
| deepseek-v4-pro (+thinking) | alan-turing, grace-hopper, margaret-hamilton, metis, momus, oracle, prometheus, coder, reviewer | ~6.500 | Orquestração pesada precisa de raciocínio profundo |
| deepseek-v4-flash | ada-lovelace, librarian, researcher, scribe | ~37.300 | Tarefas leves/rápidas com tool-use Anthropic |
| glm-5.1 | maestro | ~4.300 | Meta-orchestrator: classificação de intenção |
| mimo-v2-omni | multimodal | ~10.900 | Tarefas multimodais |
| **kimi-k2.5** | **sisyphus** | **~9.250** | Daily driver: 2.1x mais volume que glm-5.1 |
| **qwen3.5-plus** | **explore** | **~50.500** | Exploração: +35% volume, máxima throughput |
| **minimax-m2.5** | *(disponível)* | **~31.800** | Econômico: Anthropic tool-use + custo mínimo |
| **minimax-m2.7** | *(disponível)* | **~17.000** | Econômico: Anthropic tool-use intermediário |

### Princípios de roteamento

1. **Protocolo Anthropic para tool-use** — agentes que fazem muitas tool calls (bash, edit, glob) preferem MiniMax/DeepSeek via protocolo Anthropic
2. **Maximizar volume por categoria** — tarefas de alta frequência usam modelos baratos
3. **Reservar capacidade pesada** — deepseek-v4-pro+thinking apenas para orquestradores que precisam de raciocínio profundo
4. **Match complexity → cost** — nunca usar um modelo Tier A para tarefas Tier C

## Alternativas Consideradas

1. **Manter 4 modelos** — Simples, mas desperdiça 71% da capacidade da assinatura
2. **Rotear todos os 14 modelos** — Complexidade excessiva, difícil de manter, diferenças sutis entre modelos de mesmo tier
3. **Usar modelo único mais barato** — `qwen3.5-plus` para tudo — perderia qualidade em orquestração e code review

## Consequências

**Positivas:**
- Volume potencial de requests aumentou significativamente (ex: sisyphus +114%, explore +35%)
- Melhor custo-benefício: cada agente usa o modelo certo para sua complexidade
- MiniMax M2.5/M2.7 disponíveis como opções econômicas com tool-use Anthropic
- Sem custo adicional — todos os modelos já estão incluídos na assinatura

**Negativas:**
- 7 modelos = mais complexidade na config
- Modelos baratos (MiniMax, Qwen) podem ter qualidade inferior em edge cases
- Sem benchmarks próprios — decisões baseadas em documentação do provedor
- 6 modelos ainda não usados (GLM-5, Kimi K2.6, MiMo-V2-Pro, MiMo-V2.5-Pro, MiMo-V2.5, Qwen3.6 Plus)

**Riscos:**
- Se kimi-k2.5 não performar bem para sisyphus, rollback para glm-5.1 é trivial
- Se minimax-m2.5 falhar em tool-use complexo, upgrade para minimax-m2.7 ou deepseek-v4-flash

## Relacionados

- [P6 Model Strategy Plan](../../thoughts/shared/plans/p6-model-strategy.md) — plano detalhado
- [0003 — Plugin Coexistence](./0003-plugin-coexistence-strategy.md) — estratégia de camadas
- [opencode-go-guia-modelos.md](../handbooks/opencode-go-guia-modelos.md) — referência de modelos

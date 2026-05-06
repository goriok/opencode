---
name: rfc-template
description: Template de RFC (Request for Comments) para documentar decisões arquiteturais, mudanças de infraestrutura e propostas técnicas significativas. Integrado com RM-ODP viewpoints e ISO-25010. Use quando Alan Turing (Architecture phase), Ada Lovelace (Recommendations phase) ou Grace Hopper (Post-Incident phase) precisarem produzir uma decisão formal.
globs: ["**/*"]
---

# RFC Template

> Use este template para documentar qualquer decisão técnica com consequências irreversíveis, impacto em produção, ou que precise de revisão por stakeholders antes de execução.

---

## Quando Usar

- Novas fronteiras de serviço ou contratos de API
- Mudanças de topologia de infraestrutura
- Alterações no modelo de segurança ou autenticação
- Mudanças de modelo de dados com impacto em produção
- Decisões de arquitetura com tradeoffs significativos (ATAM detectado)
- Lições arquiteturais de incidentes P1/P2 (Grace Hopper Phase 7)
- Qualquer proposta que precise de aprovação antes de implementar

---

## Formato RFC

O arquivo RFC deve ser salvo em `docs/rfcs/` com o seguinte frontmatter obrigatório no topo:

```yaml
---
title: "RFC: [Título da Mudança]"
date: YYYY-MM-DD
type: rfc
status: draft | in-review | approved | rejected | superseded
authors: []
tags: []
---
```

> O corpo da RFC começa imediatamente após o frontmatter — não repita os campos acima como cabeçalho Markdown.

---

### 1. Contexto (RM-ODP View)

#### 🎯 Enterprise View (Negócio & Valor)
- **Objetivo:** [O que essa mudança alcança para o negócio]
- **Motivador:** [O problema ou oportunidade que justifica a mudança agora]

#### 🏗️ Engineering View (Técnica)
- **Solução:** [Abordagem técnica em uma frase]
- **Estratégia:** [Como será implementado — padrão, protocolo, tática arquitetural]

#### 💾 Information View (Dados)
- **Escopo:** [Quais entidades, schemas ou fluxos de dados são afetados]
- **Impacto:** [O que muda nos dados — leitura, escrita, integridade, DDL necessário?]

---

### 2. Análise de Qualidade (ISO-25010)

| Atributo | Descrição da Meta |
|---|---|
| [Característica ISO-25010] | [O que essa mudança melhora, preserva ou aceita degradar nessa dimensão] |

> Inclua apenas os atributos relevantes para esta RFC. Referência completa: Functional Suitability, Performance Efficiency, Compatibility, Usability, Reliability, Security, Maintainability, Portability.

---

### 3. Abordagem Arquitetural

Descreva a decisão arquitetural central e por que ela foi escolhida sobre as alternativas:

1. **[Passo/Componente 1]:** [Descrição]
2. **[Passo/Componente 2]:** [Descrição]
3. **[Passo/Componente 3]:** [Descrição]

**Alternativas consideradas e descartadas:**
- `[Alternativa A]` — descartada porque [razão]
- `[Alternativa B]` — descartada porque [razão]

---

### 4. Solução Técnica e Implementação

#### 🔍 Gaps Identificados

> O que existe hoje que precisa mudar. Um gap por linha.

- `[Serviço/Componente]`: [Problema atual]
- `[Serviço/Componente]`: [Problema atual]

#### 🛠️ Plano de Ação

**[Camada/Serviço 1]**
- [ ] [Tarefa concreta 1]
- [ ] [Tarefa concreta 2]

**[Camada/Serviço 2]**
- [ ] [Tarefa concreta 1]
- [ ] [Tarefa concreta 2]

---

### 5. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| [Descrição do risco] | Alta/Média/Baixa | Alto/Médio/Baixo | [Como será mitigado] |

---

### 6. Métricas de Sucesso

> Como saberemos que funcionou? Cada métrica deve ser verificável.

- [ ] [Métrica 1 — ex: redução de X% em erros 5xx durante HPA]
- [ ] [Métrica 2 — ex: zero incidentes de Y no Grafana]
- [ ] [Métrica 3 — ex: redução de OPEX em Z% em produção]

---

## Exemplos Reais

### Exemplo: Graceful Shutdown (Resiliência de Scale-Down)

```yaml
---
title: "RFC: Implementação de Graceful Shutdown"
date: 2026-04-06
type: rfc
status: approved
authors: ["Time de Plataforma"]
tags: ["resiliência", "kubernetes", "scale-down", "performance"]
---
```

**Enterprise View:** Retomar autoscaling para reduzir OPEX sem causar indisponibilidade. A mitigação atual de manter pods sobressalentes é financeiramente insustentável após Black Friday.

**Engineering View:** Interceptação ativa de sinais do SO (SIGTERM) pelo código da aplicação. O processo finaliza somente após término das transações em voo, sem depender de ajustes complexos de orquestração no K8s.

**Information View:** Proteção da integridade de transações em PostgreSQL e Redis. Garantia de commits antes do encerramento. Sem DDL necessário.

**ISO-25010:**
| Atributo | Meta |
|---|---|
| Reliability | Operações transacionais concluídas atomicamente durante shutdown |
| Performance Efficiency | Scale-down agressivo habilitado, otimizando CPU e Memória conforme carga real |

**Gaps:**
- `pa-api (Go)`: `router.Run()` bloqueante sem tratamento de `os.Signal`
- `idpa-api (Ruby)`: Falta configuração de Puma/Sidekiq para tempo de terminação

**Plano:**
- Go: `http.Server` em goroutine + `chan os.Signal` + `srv.Shutdown(ctx)` com timeout 15s
- Ruby/Puma: `config/puma.rb` para aguardar threads ativas
- Ruby/Sidekiq: flag `-t 15` para requeue de jobs não finalizados

**Riscos:**
| Risco | Mitigação |
|---|---|
| Transações > 15s excedendo timeout | Monitorar `Context Deadline Exceeded`, ajustar grace period dinamicamente |
| Sobrecarga dos pods remanescentes | `terminationGracePeriodSeconds` no K8s alinhado ao timeout da aplicação |

**Métricas:**
- [ ] Redução de 5xx durante eventos de HPA
- [ ] Redução de OPEX em produção
- [ ] Zero incidentes de "failed to wait for command to complete" no Grafana

---

## Integração com os Orquestradores

| Orquestrador | Quando Produz RFC | Fase |
|---|---|---|
| **Alan Turing** | Decisões arquiteturais com tradeoffs significativos (ATAM) | Phase 2 — Architecture |
| **Ada Lovelace** | Recomendações P1/P2 com impacto em produção | Phase 6 — Recommendations |
| **Grace Hopper** | Lições arquiteturais de incidentes P1/P2 | Phase 7 — Post-Incident Docs |

Para gerar uma RFC, invoque `/rfc-template` ou peça ao orquestrador ativo para produzir a RFC usando este template.

---

## Documentation Standards

All RFC documents produced using this template MUST follow these rules:

**Format & Location**
- File format: `.md` (Markdown only)
- Save path: `docs/rfcs/` relative to the project root
- Filename convention: `docs/rfcs/YYYY-MM-DD-titulo-kebab-case.md`

**Frontmatter (mandatory)**

Every RFC must open with the YAML frontmatter block defined in the Formato RFC section above. Fields reference:

- `type: rfc` — always fixed for RFC documents
- `status` — update as the RFC evolves: `draft` → `in-review` → `approved` / `rejected` / `superseded`
- `tags` — lowercase kebab-case; use consistent vocabulary: service names, ISO-25010 characteristics, domain (auth/infra/data/api), severity (p1/p2/p3)
- When searching for existing RFCs, grep `type: rfc` and `tags` fields first before scanning body content

**Diagrams**

All diagrams MUST be written in Mermaid using strict mode:

````markdown
```mermaid
%%{init: {"theme": "default"}}%%
%% strict mode — no implicit node creation %%
flowchart LR
    A --> B
```
````

- `flowchart LR` for architecture and data flow diagrams
- `sequenceDiagram` for service interactions and auth flows
- `erDiagram` for data model changes
- No ASCII art diagrams, no PlantUML

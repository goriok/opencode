# Agent Vocabulary & Tools Guide

> Mapping de frameworks, vocabulário e ferramentas por agente orquestrador.

## Frameworks de Referência

| Framework | Problema que resolve | Vocabulário |
|----------|-------------------|-------------|
| **IREB** | Requirements sem linguagem precisa são não-testáveis | `SHALL`, `SHOULD`, `MAY`, acceptance criteria |
| **ISO 25010** | NFRs escritos como adjetivos ("fast", "secure") não são mensuráveis | quality attributes, utility tree |
| **ATAM** | Decisões arquiteturais sem tradeoffs explícitos | Tradeoff, Sensitivity, Risk |
| **RM-ODP** | Decisões que misturam camadas são difíceis de raciocinar | Viewpoints: Computational, Engineering, Technology |
| **MADR** | ADRs sem estrutura consistente | Considered Options, Decision, Consequences |

---

## Agente → Framework Mapping

### Alan Turing (SDLC)

| Phase | Primary Framework | Secondary | Output |
|-------|-------------------|-----------|--------|
| Requirements | **IREB** | - | User stories com `SHALL`/`SHOULD` |
| Architecture | **ATAM** | RM-ODP | Tradeoff matrix |
| Design | MADR | - | ADR documents |
| Implementation | ISO 25010 | - | Quality targets |
| Testing | IREB | ISO 25010 | Testable acceptance criteria |
| Monitoring | ISO 25010 | - | Metrics dashboard |

**Vocabulário**: feature, sprint, release, user story, story point, velocity, deployment, rollback

**Ferramentas**: git, worktree, CI/CD, monitoring dashboards, APM

---

### Grace Hopper (Troubleshooting)

| Phase | Primary Framework | Secondary | Output |
|-------|-------------------|-----------|--------|
| Detection | ISO 25010 | - | Availability metrics |
| Triage | RM-ODP | - | Layer identification |
| RCA | ATAM | - | Risk/Sensitivity analysis |
| Fix | IREB | - | Testable fix criteria |
| Prevention | ISO 25010 | - | Regression tests |

**Vocabulário**: incident, RCA, MTTR, MTBF, severity, priority, hotfix, rollback, degradation, recovery

**Ferramentas**: logs, metrics, tracing, debugger, profiler, alerting

---

### Margaret Hamilton (Deep Analysis)

| Phase | Primary Framework | Secondary | Output |
|-------|-------------------|-----------|--------|
| Scope | **ISO 25010** | IREB | Utility tree, quality attributes |
| Decomposition | RM-ODP | - | Viewpoint map |
| Investigation | ATAM | - | Tradeoff matrix |
| Synthesis | ISO 25010 | - | Quality profile |
| Recommendations | **MADR** | ATAM | Ranked ADRs |
| Validation | IREB | - | Testable criteria |

**Vocabulário**: quality attribute, tradeoff, sensitivity point, risk, quality profile, viewpoint, ADR, consequence

**Ferramentas**: code analysis, performance profiling, security scanning, data exploration

---

### Ada Lovelace (Exploratory)

| Phase | Framework | Output |
|-------|----------|--------|
| Quick Scope | Ad-hoc | 1-2 sentence scope |
| Probe | Pattern matching | 2-3 questions |
| Discover | - | Patterns identified |
| Insight | - | 3-5 bullet points |

**Vocabulário**: pattern, insight, anomaly, correlation, quick look, snapshot

**Ferramentas**: grep, search, quick analysis (sem formal frameworks)

---

## Quick Reference: Quando Usar Qual Framework

| Situação | Framework |
|----------|-----------|
| Escrever requisito | IREB (`SHALL`/`SHOULD`) |
| Definir NFR | ISO 25010 (quality attribute) |
| Decisão arquitetural | ATAM + RM-ODP |
| Documentar decisão | MADR |
| Analisar incidente | ATAM (RCA) |
| Requirements flexíveis | IREB (MAY) |
| Exploração rápida | Nenhum (ada-lovelace) |

---

## Vocabulário por Agente

### Alan Turing

```
feature, epic, user story, task
sprint, release, milestone
backlog, refinement, planning poker
deployment, rollback, CI/CD
code review, PR, merge
```

### Grace Hopper

```
incident, outage, degradation
RCA, root cause, blast radius
MTTR, MTBF, SLA
severity (SEV1-4), priority (P1-4)
hotfix, patch, workaround
```

### Margaret Hamilton

```
quality attribute, tradeoff, sensitivity
risk, quality profile, utility tree
viewpoint, ADR, consequence
ISO-25010, ATAM, RM-ODP
```

### Ada Lovelace

```
pattern, insight, anomaly
quick look, snapshot
correlation, trend
```

---

*Guia de vocabulário e ferramentas por agente*
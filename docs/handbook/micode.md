# micode — Brainstorm → Plan → Implement Workflow

> Plugin com workflow estruturado Brainstorm → Plan → Implement e continuidade de sessão

## Overview

`micode` é um plugin que impõe disciplina ao fluxo de trabalho do OpenCode. Ele enforce um lifecycle obrigatório de 3 estágios:

```
Brainstorm → Plan → Implement
     ↓         ↓        ↓
  research  research  executor
```

O problema que resolve: agentes AI são "preguiçosos" por natureza — querem pular direto para implementação. micode enforce uma estrutura que produz resultados confiáveis.

## Core Features

| Feature | Descrição |
|---------|----------|
| **3-Stage Lifecycle** | Brainstorm → Plan → Implement obrigatório |
| **Parallel Research** | Múltiplos subagentes em paralelo |
| **TDD Workflow** | Test-first development |
| **Git Worktree Isolation** | Implementação isolada |
| **Implementer + Reviewer Pairs** | Verificação dupla por task |
| **Session Continuity** | Continuity via ledgers |
| **mindmodel Integration** | Project-specific pattern enforcement |

## Princípios Fundamentais

1. **Brainstorm first** — Refine ideias antes de codar
2. **Research before implementing** — Entenda o codebase
3. **Plan with human buy-in** — Pegue aprovação antes de codar
4. **Parallel investigation** — múltiplos subagentes
5. **Isolated implementation** — Use git worktrees
6. **Continuous verification** — Implementer + Reviewer
7. **Session continuity** — Never lose context

## Installation

```json
{
  "plugin": ["micode"]
}
```

## Workflow Estruturado

### 1. Brainstorm (O "O Que" e "Por Que")

Subagentes de pesquisa paralelos exploram o codebase, fazem perguntas clarificadoras, e consideram múltiplas arquiteturas.

**Output**: `thoughts/shared/designs/YYYY-MM-DD-{topic}-design.md`

```
## 🎯 Design Title

### Problem
[Descrição do problema]

### Approaches Considered
[Abordagens exploradas]

### Proposed Solution
[Solução proposta com justificativa]

### Trade-offs
[Trade-offs identificados]
```

### 2. Plan (O "Como")

Agente especializado transforma o design em tasks determinísticas (2-5 min cada) com caminhos de arquivo exatos e expectativas test-first.

**Output**: `thoughts/shared/plans/YYYY-MM-DD-{topic}.md`

```
## 📋 Plan: [Feature]

### Overview
[Resumo]

### Tasks
1. [ ] Task description (2-5 min)
    - File: `src/path/file.ts`
    - Test: `tests/file.test.ts`
    - Pre-req: [task id]

### Acceptance Criteria
- [ ] Critério 1
- [ ] Critério 2
```

**⚠️ Get approval antes de implementar** — Mostre o plano e espere aprovação humana.

### 3. Implement (Execução)

micode cria Implementer-Reviewer pairs em paralelo (10-20 micro-tasks simultâneas) usando git worktrees isolados. Cada par segue TDD estrito:

1. Escreve o teste → vÊ falha
2. Escreve o código → vÊ passar
3. Reviewer verifica → Aprova ou rejeita

## Agentes Disponíveis

| Agente | Propósito |
|--------|-----------|
| **commander** | Orchestrator principal |
| **brainstormer** | Design exploration |
| **planner** | Implementation plans |
| **executor** | Orchestrates implement→review |
| **implementer** | Execute tasks |
| **reviewer** | Check correctness |
| **codebase-locator** | Find file locations |
| **codebase-analyzer** | Deep code analysis |
| **pattern-finder** | Find existing patterns |
| **project-initializer** | Generate project docs |
| **ledger-creator** | Continuity ledgers |
| **artifact-searcher** | Search past work |

## Decision Tree

O Commander usa uma decision tree para escolhero workflow:

```
0. Call mindmodel_lookup for project patterns → ALWAYS
1. Can I do this in under 2 minutes? → Just do it
2. Can I hold the whole change in my head? → Brief plan, then execute
3. Multiple unknowns or significant scope? → Full workflow
```

## Quick Mode

Para tasks triviais, usa modoquick:

```
Trivial tasks: Just do it directly
- Fix a typo
- Update a version number
- Add a simple log statement
- Fix obvious bugs

Small tasks: Brief plan, then execute
- Add simple function (< 20 lines)
- Add test for existing code
- Fix failing test

Complex tasks: Full workflow
- New feature with multiple components
- Architectural changes
- Changes touching 5+ files
- Unclear requirements
```

## Session Continuity

micode preserva contexto entre sessões usando ledgers:

```
thoughts/ledgers/CONTINUITY_{session-name}.md
```

O sistema atualiza automaticamente ao atingir ~70% de uso de contexto.

## mindmodel Integration

micode usa `.mindmodel/` do projeto para:

- Pattern enforcement
- Naming conventions
- Architecture constraints
- Error handling patterns
- Testing patterns

**⚠️ ALWAYS call mindmodel_lookup BEFORE writing code**

## Git Worktree Integration

Para implementation isolada:

```bash
# Criar worktree para feature
git worktree add ../feature-name -b feature/feature-name

# Todo trabalho no worktree feature/
# Nunca no main
```

Vantagens:
- Isolamento total
- Não interfere no branches principais
- easy cleanup

## Configuration

Crie `~/.config/opencode/micode.jsonc`:

```json
{
  "decision_tree": {
    "trivial_threshold_minutes": 2,
    "small_threshold_files": 1
  },
  
  "parallelism": {
    "max_concurrent_tasks": 10,
    "fire_and_check": true
  },
  
  "worktree": {
    "default_base": "main",
    "auto_cleanup": false
  },
  
  "tdd": {
    "enabled": true,
    "test_extension": ".test.ts"
  },
  
  "ledger": {
    "trigger_at_context_percent": 70,
    "path": "thoughts/ledgers"
  },
  
  "mindmodel": {
    "required_before_code": true,
    "patterns": ["naming", "error-handling", "testing"]
  }
}
```

## Skills Incluídas

| Skill | Descrição |
|-------|----------|
| `agents-feature-builder** | Orquestra squad técnica |
| `agents-troubleshooter** | Diagnostica e corrige |
| `explain-concept** | Explica conceitos |
| `plan-mode** | Modo planejamento |

## Quando Usar micode

✅ **Use quando:**
- Quer workflow estruturado brainstorm→plan→implement
- Prefere TDD-driven implementation
- Precisa project-specific pattern enforcement
- Quer alta paralelização (10-20 micro-tasks)
- Valoriza session continuity

❌ **Não use quando:**
- Quick fixes simples
- Explorações sem resultado definido
- Sessions one-off sem continuidade

## Repositório

- GitHub: https://github.com/vtemian/micode
- Blog: https://blog.vtemian.com/project/micode/
- npm: https://www.npmjs.com/package/micode

---

*Parte do handbook de plugins OpenCode*
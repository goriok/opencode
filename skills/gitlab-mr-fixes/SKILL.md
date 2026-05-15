---
name: gitlab-mr-fixes
description: Aplica correções em MRs do GitLab após review — implementa mudanças no código, responde comentários de reviewers, aplica sugestões, e valida RED->GREEN quando há testes envolvidos. Invocar com a URL do MR.
disable-model-invocation: true
argument-hint: <gitlab-mr-url>
tool: opencode-only
---

# GitLab MR Fixes

Skill especializada em **implementar** as correções apontadas em um MR do GitLab —
complementar à `gitlab-mr-review`, que faz o review e publica findings.

Esta skill cobre três responsabilidades distintas:

1. **Aplicar correções no código** — alterar arquivos na branch do MR via GitLab API
2. **Responder comentários de reviewers** — publicar replies fundamentadas nos threads do MR
3. **Validar RED→GREEN** — executar/adaptar testes para provar que as correções funcionam

---

## Quando Ativar

- Usuário pede para "corrigir o MR", "aplicar as sugestões", "responder os comentários"
- Há findings de uma `gitlab-mr-review` anterior que precisam ser implementados
- Reviewer deixou comentários no MR e o usuário quer endereçá-los
- Usuário quer confirmar que os testes cobrem as mudanças feitas

---

## Workflow

### ESTÁGIO 0 — Contexto do MR

Parsear a URL do MR (se fornecida) ou usar o contexto da sessão:

- `project_id` = namespace path (ex: `grupo/projeto`) — nunca double-encode
- `mr_iid` = número do MR na URL
- `source_branch` = branch onde aplicar as correções

Buscar estado atual:

```
gitlab_get_merge_request(project_id, merge_request_iid: mr_iid)
```

Buscar comentários abertos (threads de review + overview notes):

```
gitlab_mr_discussions(project_id, merge_request_iid: mr_iid)
gitlab_get_merge_request_notes(project_id, merge_request_iid: mr_iid, sort: asc)
```

Categorizar o que existe:

- **Threads inline** (aba Changes) — `type: "DiffNote"`, têm `position`
- **Overview notes** (aba Overview) — `type: null`, sem `position`, não-system
- **System notes** — `system: true` — ignorar (são eventos automáticos do GitLab)

---

### ESTÁGIO 1 — Análise das Correções

Para cada comentário/thread não-system, classificar:

| Tipo                           | Ação                                               |
| ------------------------------ | -------------------------------------------------- |
| Sugestão de mudança de código  | Implementar via `gitlab_create_or_update_file`     |
| Pergunta sobre decisão técnica | Redigir resposta fundamentada                      |
| Nitpick / style                | Avaliar se vale corrigir ou justificar por que não |
| Bug apontado                   | Corrigir + adicionar teste se aplicável            |
| Aprovação / LGTM               | Registrar, sem ação necessária                     |

Antes de implementar qualquer correção:

1. Ler o arquivo atual na `source_branch` via `gitlab_get_file_contents` (com `ref: source_branch`)
2. Capturar `last_commit_id` do arquivo para uso no update
3. Entender o contexto completo (não apenas o hunk do diff)

---

### ESTÁGIO 2 — Aplicar Correções no Código

Para cada correção de código identificada:

```
gitlab_create_or_update_file(
  project_id:     <project_id>
  file_path:      <caminho do arquivo>
  branch:         <source_branch>
  content:        <conteúdo completo atualizado>
  commit_message: <mensagem seguindo Conventional Commits>
  last_commit_id: <last_commit_id do arquivo lido>
)
```

**Regras para o commit message:**

- Seguir Conventional Commits sem scope: `fix:`, `test:`, `refactor:`, etc.
- Referenciar o ticket/issue se conhecido (ex: `Refs: TST-81EA`)
- Uma correção por commit se as mudanças forem independentes
- Agrupar em um único commit se as mudanças forem parte do mesmo contexto

**Regras para o conteúdo:**

- Sempre passar o arquivo **completo** — a API substitui o arquivo inteiro
- Nunca truncar ou omitir partes não alteradas
- Preservar encoding, line endings e permissões do arquivo original

---

### ESTÁGIO 3 — Validação RED→GREEN (quando há testes)

Quando a correção envolve comportamento testável:

1. **Identificar os testes existentes** relacionados à mudança
2. **Rodar os testes localmente** para confirmar que passam após a correção:
   ```bash
   # Exemplos — adaptar ao stack do projeto
   bash scripts/test-nginx.sh
   npm test
   pytest tests/
   ```
3. **Se os testes falharem:**
   - Diagnosticar a causa (bug no teste vs bug na implementação)
   - Corrigir — nunca enfraquecer um teste para forçar um PASS
   - Aplicar correção no código ou no teste conforme apropriado
4. **Confirmar RED→GREEN:**
   - Rodar com config antiga (ou config mock do estado anterior) → deve FAIL nos critérios corrigidos
   - Rodar com config nova → deve PASS em todos

**Circuit breaker:** se os testes falharem 3 vezes consecutivas sem progresso claro, parar e pedir mais contexto ao usuário. Não tentar correções às cegas.

---

### ESTÁGIO 4 — Responder Comentários

Para cada comentário que precisa de resposta (threads inline ou overview notes):

#### Threads inline (aba Changes)

Responder dentro do thread existente:

```
gitlab_create_merge_request_discussion_note(
  project_id:        <project_id>
  merge_request_iid: <mr_iid>
  discussion_id:     <id do thread>
  body:              <resposta>
)
```

Se a correção foi implementada, resolver o thread após responder:

```
gitlab_resolve_merge_request_thread(
  project_id:        <project_id>
  merge_request_iid: <mr_iid>
  discussion_id:     <id do thread>
  resolved:          true
)
```

#### Overview notes (aba Overview)

Responder com uma nova nota geral:

```
gitlab_create_merge_request_note(
  project_id:        <project_id>
  merge_request_iid: <mr_iid>
  body:              <resposta>
)
```

---

## Formato das Respostas

### Resposta a sugestão implementada

```
Implementado em <commit_sha_curto> — <resumo da mudança>.

<Explicação de 1-3 linhas sobre o que foi feito e por quê, se necessário.>
```

### Resposta a sugestão não implementada (com justificativa)

```
Mantivemos a abordagem atual por <razão técnica objetiva>.

<Explicação de 2-4 linhas. Referenciar docs, RFC, ou comportamento específico
do sistema se aplicável. Se for ponto válido para PR futuro, mencionar.>
```

### Resposta a pergunta técnica

```
<Resposta direta à pergunta.>

<Contexto adicional se necessário — máximo 4 linhas. Sem jargão desnecessário.>
```

**Regras de tom:**

- Objetivo e técnico — sem linguagem defensiva ou apologética
- Citar evidência quando possível (número de test, commit, doc externa)
- Não repetir o comentário do reviewer na resposta
- Se discordar, explicar o raciocínio técnico claramente

---

## Regras Críticas

1. **Ler antes de escrever** — sempre buscar o arquivo atual com `gitlab_get_file_contents` antes de qualquer update. Nunca escrever baseado apenas no diff.

2. **`last_commit_id` obrigatório em updates** — usar sempre o `last_commit_id` retornado pelo `get_file_contents` para evitar conflitos.

3. **Conteúdo completo** — a API substitui o arquivo inteiro. Nunca enviar conteúdo parcial.

4. **Conventional Commits** — mensagens de commit seguem o padrão da skill `conventional-commits` (sem scope, imperativo, ≤ 72 chars na primeira linha).

5. **Nunca enfraquecer testes** — se um teste falha após a correção, o problema é na implementação, não no teste. Ajustar o teste só se ele estiver errado conceitualmente.

6. **Resolver threads após corrigir** — quando um thread inline pede uma mudança que foi implementada, resolver o thread (`resolved: true`) após publicar a resposta.

7. **Não resolver threads de dúvida** — threads que são perguntas sem resposta implementada não devem ser resolvidos — apenas respondidos.

8. **`iid` não `id`** — usar sempre o `iid` do MR (número na URL).

9. **Nunca double-encode `project_id`** — passar o namespace path como string simples.

---

## Anti-patterns

- ❌ Editar arquivos sem ler o conteúdo atual primeiro
- ❌ Omitir `last_commit_id` no update (causa conflito ou sobrescreve commits recentes)
- ❌ Enviar conteúdo parcial no `content` do update
- ❌ Resolver threads que ainda têm perguntas abertas sem resposta
- ❌ Alterar testes para forçar PASS sem entender a causa da falha
- ❌ Publicar respostas defensivas ou apologéticas — manter tom técnico e objetivo
- ❌ Fazer mudanças em arquivos não relacionados à correção solicitada
- ❌ Commitar `test-nginx.sh` ou arquivos de teste temporários na raiz do projeto

---

## Coexistência com `gitlab-mr-review`

| Skill              | Responsabilidade                                                 |
| ------------------ | ---------------------------------------------------------------- |
| `gitlab-mr-review` | Ler o diff, fazer review, publicar findings como draft notes     |
| `gitlab-mr-fixes`  | Implementar correções, responder comentários, validar com testes |

**Fluxo típico:**

1. `gitlab-mr-review <url>` → gera findings e publica no MR
2. Desenvolvedor ou `gitlab-mr-fixes <url>` → implementa as correções e responde os threads

As duas skills podem ser usadas independentemente — `gitlab-mr-fixes` funciona com qualquer
comentário no MR, não apenas os gerados pela `gitlab-mr-review`.

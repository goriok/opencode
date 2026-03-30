---
name: gitlab-mr-review
description: Orquestra code review em MRs do GitLab — busca o diff via MCP, aplica a skill code-review sobre ele, e publica os findings como inline threads e overview note usando draft notes. Invocar com a URL do MR.
disable-model-invocation: true
argument-hint: <gitlab-mr-url>
---

# GitLab MR Review

Skill orquestradora que une o processo de code review com a publicação dos resultados
diretamente no GitLab MR como comentários inline (aba **Changes**) e nota geral (aba **Overview**).

## Quando Ativar

Ativar quando o usuário fornecer uma URL de GitLab MR e pedir para revisar ou comentar o MR.
Exemplos de URLs aceitas:

```
https://gitlab.com/grupo/projeto/-/merge_requests/42
https://gitlab.empresa.com/grupo/subgrupo/projeto/-/merge_requests/7
```

## Workflow — Três Estágios

### ESTÁGIO 1 — Coleta de Dados do MR

**1.1 Parsear a URL do MR**

A partir da URL fornecida em `$ARGUMENTS`:
- `project_id` = tudo entre o host e `/-/merge_requests/`, ex: `grupo/projeto` ou `grupo/subgrupo/projeto`
  - Passar o path string como está — **NÃO double-encode** (a tool faz o encoding internamente)
- `mr_iid` = o número inteiro no final da URL
- Exemplo: `https://gitlab.com/turia/idpa/-/merge_requests/42` → `project_id = "turia/idpa"`, `mr_iid = "42"`

**1.2 Buscar metadata do MR**

```
gitlab_get_merge_request(project_id, merge_request_iid: mr_iid)
```

Extrair e guardar:
- `diff_refs.base_sha`
- `diff_refs.head_sha`
- `diff_refs.start_sha`
- `title` (para o cabeçalho do overview)
- `source_branch`

**Guard:** se `diff_refs` for `null` (MR sem commits ainda), abortar e informar o usuário.

**1.3 Buscar diffs dos arquivos**

```
gitlab_get_merge_request_diffs(project_id, merge_request_iid: mr_iid)
```

Retorna array de objetos por arquivo:
```json
{
  "old_path": "app/models/user.rb",
  "new_path": "app/models/user.rb",
  "diff": "<unified diff text>",
  "new_file": false,
  "renamed_file": false,
  "deleted_file": false
}
```

**1.4 Construir mapa de linhas por arquivo**

Para cada arquivo, parsear o campo `diff` (formato unified diff) e construir um mapa
`linha_lógica → { old_line, new_line, type }`:

```
Regras de parsing:
  @@ -old_start,count +new_start,count @@  → inicializar contadores
  linha com " " (espaço)  = contexto  → old_line++, new_line++  (type: "context")
  linha com "-"           = removida  → old_line++              (type: "old")
  linha com "+"           = adicionada → new_line++             (type: "new")
  linha com "\"           = no newline at end of file → ignorar
```

Este mapa será consultado no Estágio 3 para resolver findings em posições do diff.

---

### ESTÁGIO 2 — Code Review

Aplicar **todo o processo e critérios da skill `code-review`** sobre o diff obtido no Estágio 1.

- O contexto de review são os arquivos e diffs retornados por `gitlab_get_merge_request_diffs`
- Ler o conteúdo completo de cada arquivo alterado via `gitlab_get_file_contents` se necessário para contexto adicional
- Aplicar todas as categorias de review, severidades e guardrails definidos na skill `code-review`
- Gerar os findings no formato padrão da skill `code-review`:

```
🔴 BLOCKER — arquivo:linha: descrição
🟡 WARNING — arquivo:linha: descrição
🟢 SUGGESTION — arquivo:linha: descrição
ℹ️  INFO — descrição
```

- **Cada finding deve ter**: severidade, arquivo (new_path), número de linha lógica no novo arquivo, descrição
- Findings sem linha precisa (ex: arquiteturais, de configuração) ficam marcados como `line: null`

---

### ESTÁGIO 3 — Publicação no GitLab

#### 3.1 Mapear findings para posições do diff

Para cada finding com `arquivo` e `linha`:

1. Consultar o mapa de linhas do arquivo construído no Estágio 1
2. Se a linha está no mapa → resolver `old_line` / `new_line` conforme o tipo:
   - Linha **adicionada** (`type: "new"`): `new_line = N`, `old_line = null`
   - Linha **removida** (`type: "old"`): `old_line = N`, `new_line = null`
   - Linha de **contexto** (`type: "context"`): ambos preenchidos
3. Se a linha **não está no mapa** (fora dos hunks do diff) → acumular no overflow do overview

#### 3.2 Criar draft notes inline (por finding com posição)

Para cada finding com posição resolvida:

```
gitlab_create_draft_note(
  project_id:        <project_id>
  merge_request_iid: <mr_iid>
  body: "<comentário formatado — ver seção Formato dos Comentários>"
  position: {
    base_sha:       <diff_refs.base_sha>
    head_sha:       <diff_refs.head_sha>
    start_sha:      <diff_refs.start_sha>
    position_type:  "text"
    new_path:       <arquivo new_path>
    old_path:       <arquivo old_path>
    new_line:       <int ou null>
    old_line:       <int ou null>
  }
)
```

Se `gitlab_create_draft_note` falhar para um inline (ex: linha inválida), mover o finding
para o overflow do overview — nunca abortar o fluxo inteiro por um finding.

#### 3.3 Criar draft note de overview (sem posição)

Após todos os inline notes, criar **uma** draft note geral sem `position`:

```
gitlab_create_draft_note(
  project_id:        <project_id>
  merge_request_iid: <mr_iid>
  body: "<sumário formatado — ver seção Formato do Overview>"
)
```

#### 3.4 Preview e confirmação

Antes de publicar, exibir ao usuário:

```
Pronto para publicar no MR !{mr_iid} — "{título}":

  • {N} inline comments (aba Changes)
  • 1 overview note (aba Overview)

Resumo dos findings:
  🔴 BLOCKER:    {n}
  🟡 WARNING:    {n}
  🟢 SUGGESTION: {n}
  ℹ️  INFO:       {n}

Posso publicar todos os comentários?
```

Aguardar confirmação explícita do usuário. Se negado, descartar os drafts via
`gitlab_delete_draft_note` para cada draft criado, ou informar que os drafts
ficam salvos no GitLab e podem ser gerenciados pelo usuário.

#### 3.5 Bulk publish

Somente após confirmação:

```
gitlab_bulk_publish_draft_notes(
  project_id:        <project_id>
  merge_request_iid: <mr_iid>
)
```

Retorna `[]` (array vazio) em caso de sucesso — isso é normal (HTTP 204).

---

## Formato dos Comentários

### Inline (aba Changes)

```
{emoji_severidade} **[{SEVERIDADE}]** {descrição concisa}

{explicação do problema em 2-4 linhas}
{sugestão de correção quando aplicável}
```

Exemplos:

```
🔴 **[BLOCKER]** N+1 query em `UsersController#index`.

`user.roles` é acessado no serializer sem eager loading.
Adicione `.includes(:roles)` à query antes de passar para AMS.
Sem isso, cada usuário serializado dispara um SELECT extra.
```

```
🟡 **[WARNING]** Controller retorna JSON sem serializer AMS.

`render json: @user.to_json` bypassa o `UserSerializer`.
Use `render json: @user, serializer: UserSerializer`.
```

### Overview Geral (aba Overview)

```markdown
## Code Review — MR !{mr_iid}: "{título}"

> Branch: `{source_branch}`

| Severidade     | Qtd |
|----------------|-----|
| 🔴 BLOCKER     |  N  |
| 🟡 WARNING     |  N  |
| 🟢 SUGGESTION  |  N  |
| ℹ️  INFO        |  N  |

{Se houver findings sem localização precisa no diff:}
### Findings sem localização no diff

- 🟡 **[WARNING]** `app/services/user_service.rb`: descrição do finding

{Sumário final}
---
**Veredicto:** {ready to merge | necessita correções antes do merge}
```

---

## Regras Críticas

1. **Sempre draft first** — usar `gitlab_create_draft_note` para tudo; nunca `gitlab_create_merge_request_thread` diretamente. Drafts permitem bulk-publish atômico e preview.

2. **Confirmar antes de publicar** — `gitlab_bulk_publish_draft_notes` só após confirmação explícita do usuário.

3. **Null-guard em `diff_refs`** — se o MR não tem commits, abortar com mensagem clara.

4. **Nunca double-encode o `project_id`** — passar o namespace path como string simples (`grupo/projeto`), a tool faz o encoding.

5. **`iid` não `id`** — usar sempre o `iid` do MR (número na URL), nunca o `id` global.

6. **Fallback para overflow** — se um finding não pode ser mapeado para uma posição válida no diff, incluí-lo no overview em vez de abortar.

7. **Bulk-publish por último** — criar todos os drafts (inline + overview) antes de chamar o bulk-publish.

8. **Somente linhas do diff** — não comentar em linhas fora dos hunks alterados. O GitLab rejeita posições fora do diff.

9. **O review é da skill `code-review`** — esta skill não define critérios de review; ela orquestra. Todos os critérios, categorias e guardrails vêm da skill `code-review`.

---

## Anti-patterns

- ❌ Chamar `gitlab_bulk_publish_draft_notes` sem preview e confirmação
- ❌ Tentar postar inline em linhas fora dos hunks do diff (GitLab retorna erro 400)
- ❌ Publicar findings de INFO como inline — INFO vai apenas no overview
- ❌ Criar uma nova thread por finding de overview — um único `gitlab_create_draft_note` sem position para o sumário inteiro
- ❌ Ler apenas o diff sem buscar o arquivo completo quando o contexto for insuficiente para o review
- ❌ Usar `line_range` no position sem ter o `line_code` SHA correto — omitir `line_range` para comentários de linha única

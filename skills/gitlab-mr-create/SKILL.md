---
name: gitlab-mr-create
description: Cria um Merge Request no GitLab — coleta metadados da branch, gera título, descrição e changelog no template padrão, e abre o MR via API. Invocar com o project_id ou URL do projeto.
disable-model-invocation: true
argument-hint: <gitlab-project-url-or-id> [target-branch]
---

# GitLab MR Create

Skill responsável por criar um Merge Request no GitLab com título, descrição e
changelog gerados automaticamente a partir do diff entre a branch atual e a branch alvo.

> **Escopo desta skill:** apenas criação do MR com descrição padronizada.
> Para revisar um MR existente → `gitlab-mr-review`.
> Para implementar correções em um MR → `gitlab-mr-fixes`.
>
> | Skill               | Faz                                                        |
> | ------------------- | ---------------------------------------------------------- |
> | `gitlab-mr-create`  | Analisa diff → gera descrição → cria o MR                  |
> | `gitlab-mr-review`  | Lê diff → review → publica findings como draft notes       |
> | `gitlab-mr-fixes`   | Implementa correções → responde comentários → valida testes |

---

## Quando Ativar

Ativar quando o usuário pedir para **criar**, **abrir** ou **submeter** um MR/PR no GitLab.

Exemplos de invocação:

```
/gitlab-mr-create grupo/projeto
/gitlab-mr-create https://gitlab.empresa.com/grupo/projeto/-/merge_requests
/gitlab-mr-create grupo/projeto main
```

---

## Workflow — Três Estágios

### ESTÁGIO 1 — Coleta de Dados

**1.1 Parsear os argumentos**

A partir de `$ARGUMENTS`:

- `project_id` = namespace path (ex: `grupo/projeto`) ou extraído da URL
  - Se URL fornecida: extrair o path entre o host e `/-/`
  - Passar como string simples — **NÃO double-encode**
- `target_branch` = segundo argumento se fornecido; caso contrário, inferir no passo 1.3

**1.2 Buscar metadados do projeto**

```
gitlab_get_project(project_id)
```

Extrair:
- `default_branch` (usado como `target_branch` se não fornecido)
- `name` e `path_with_namespace` (para referência)

**1.3 Identificar a source branch**

```
gitlab_list_branches(project_id)  // ou inferir do contexto local via git
```

Se o contexto local estiver disponível (`git rev-parse --abbrev-ref HEAD`), usar a branch atual.
Caso contrário, perguntar ao usuário qual branch usar como source.

**Guard:** se `source_branch == target_branch`, abortar com mensagem clara.

**1.4 Buscar o diff entre as branches**

```
gitlab_get_branch_diffs(
  project_id: <project_id>
  from: <target_branch>
  to: <source_branch>
)
```

Se o diff estiver vazio (nenhum commit novo), abortar com:
> "Nenhuma diferença encontrada entre `<source_branch>` e `<target_branch>`. Verifique se há commits na branch."

**1.5 Buscar commits da branch**

```
gitlab_list_commits(
  project_id: <project_id>
  ref_name:   <source_branch>
)
```

Filtrar apenas os commits que estão na source e não na target (usar os SHAs do diff como referência).

---

### ESTÁGIO 2 — Geração da Descrição

Analisar o diff e os commits para gerar o conteúdo do MR no template padrão abaixo.

#### Template de Descrição

```markdown
## Merge Request

### What changed
<Parágrafo de 2-5 linhas descrevendo o que foi implementado ou alterado, em linguagem
técnica mas acessível. Explicar a mudança principal e listar as sub-alterações relevantes
em bullets se houver mais de uma.>

### Por que esta mudança é necessária?
<Parágrafo de 2-4 linhas explicando a motivação técnica ou de negócio. Focar no "por quê",
não repetir o "o quê" do bloco anterior.>

---

## Changelog

### Added
<Lista de itens novos adicionados. Formato: `arquivo/componente: descrição do que foi adicionado.`>

### Changed
<Lista de itens existentes que foram modificados. Formato: `arquivo/componente: descrição da mudança.`>

### Fixed
<Lista de bugs corrigidos. Formato: `arquivo/componente: descrição do fix.` Omitir seção se vazia.>

### Removed
<Lista de itens removidos. Formato: `arquivo/componente: descrição do que foi removido.` Omitir seção se vazia.>
```

**Regras de geração:**

- Escrever na linguagem do projeto (se commits/código estiverem em PT-BR, usar PT-BR; se EN, usar EN)
- "What changed" deve ser informativo — evitar frases genéricas como "foram feitas alterações"
- "Por que esta mudança é necessária?" deve justificar do ponto de vista técnico ou funcional
- Changelog: listar apenas seções com itens; omitir `Fixed` e `Removed` se vazias
- Cada item do changelog deve identificar o arquivo ou componente afetado
- Não inventar informações não presentes no diff — basear-se apenas no que foi alterado

**Inferência do título:**

- Formato: `<tipo>: <descrição imperativa breve>` seguindo Conventional Commits
- Tipos: `feat`, `fix`, `refactor`, `test`, `chore`, `docs`, `ci`
- Máximo 72 caracteres
- Exemplos:
  - `feat: adiciona lógica de refresh window na validação de tokens JWT`
  - `fix: corrige race condition no worker de processamento de eventos`

---

### ESTÁGIO 3 — Criação do MR

**3.1 Preview e confirmação**

Exibir ao usuário antes de criar:

```
Pronto para criar o MR em <project_id>:

  Título:         <título gerado>
  Source branch:  <source_branch>
  Target branch:  <target_branch>
  Draft:          <Sim | Não>

  Descrição:
  ──────────────────────────────────────
  <primeiras 10 linhas da descrição>
  ...
  ──────────────────────────────────────

Posso criar o MR com estas informações?
```

Aguardar confirmação. Se o usuário solicitar ajustes, atualizar título ou descrição antes de criar.

**3.2 Criar o MR**

```
gitlab_create_merge_request(
  project_id:    <project_id>
  title:         <título gerado ou ajustado>
  description:   <descrição no template>
  source_branch: <source_branch>
  target_branch: <target_branch>
  draft:         <true se solicitado pelo usuário, false por padrão>
  remove_source_branch: false
  squash:        false
)
```

**3.3 Confirmar criação**

Após criar com sucesso, exibir:

```
MR criado com sucesso: !<iid> — "<título>"
URL: <web_url>
```

---

## Regras Críticas

1. **Preview antes de criar** — sempre mostrar título + prévia da descrição e aguardar confirmação antes de chamar `gitlab_create_merge_request`.

2. **Nunca double-encode `project_id`** — passar namespace path como string simples (`grupo/projeto`).

3. **`iid` não `id`** — ao referenciar MRs existentes, usar sempre o `iid`.

4. **Basear-se apenas no diff** — não inventar informações não presentes nas mudanças.

5. **Draft por padrão: não** — criar como MR pronto para review salvo se o usuário pedir explicitamente draft.

6. **Guard de branch idêntica** — se `source_branch == target_branch`, abortar antes de gerar descrição.

7. **Guard de diff vazio** — se não há commits entre as branches, abortar com mensagem clara.

8. **Conventional Commits no título** — o título do MR deve seguir o padrão `tipo: descrição`.

---

## Anti-patterns

- ❌ Criar o MR sem preview e confirmação do usuário
- ❌ Inventar itens no changelog não presentes no diff
- ❌ Usar frases genéricas em "What changed" sem descrever as mudanças reais
- ❌ Omitir "Por que esta mudança é necessária?" — sempre justificar a motivação
- ❌ Double-encode do `project_id` na chamada da API
- ❌ Criar MR com `source_branch == target_branch`
- ❌ Ignorar o idioma do projeto — respeitar PT-BR ou EN conforme o contexto do código

---

## Coexistência com as outras skills GitLab

**Fluxo típico completo:**

1. `gitlab-mr-create <projeto>` → analisa diff, gera descrição, cria o MR
2. `gitlab-mr-review <url-do-mr>` → faz review e publica findings no MR recém-criado
3. `gitlab-mr-fixes <url-do-mr>` → implementa correções e responde os comentários

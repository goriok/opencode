---
name: change-request-create
description: Cria uma Change Request (CR) consolidada em docs/change_requests/ a partir dos commits e MRs mergeados desde a última tag git. Invocar quando o usuário pedir para criar, gerar ou documentar uma CR de mudança.
disable-model-invocation: true
argument-hint: [período ou tag base opcional]
allowed-tools: Read, Grep, Glob, Bash
---

# Change Request Create

Gera o arquivo de Change Request consolidado para o período desde a última tag git (ou tag informada via `$ARGUMENTS`).

## Quando Ativar

Ativar quando o usuário:

- Pedir para criar uma CR, change request ou GMUD
- Pedir para documentar as mudanças desde a última release/tag
- Usar frases como "gera a CR", "cria a change request", "documenta as mudanças para deploy"

## Passos de Execução

### 1. Determinar o período

```bash
# Obter a tag base (última tag ou a fornecida em $ARGUMENTS)
git tag --sort=-version:refname | head -1

# Listar commits desde a tag (sem merges)
git log <TAG>..HEAD --format="%H %s" --no-merges

# Listar merge commits para extrair MR IIDs
git log <TAG>..HEAD --format="%H %s" --merges
```

Se `$ARGUMENTS` for fornecido, usar como tag base em vez da última tag.

### 2. Coletar MRs via GitLab API

- Usar `gitlab_list_merge_requests` com `state=merged`, `target_branch=main` (ou branch padrão)
- Filtrar apenas os MRs cujos `merge_commit_sha` estão entre `<TAG>..HEAD`
- Coletar: `iid`, `title`, `web_url`, `author.name`, `merged_at`

### 3. Determinar sistemas envolvidos

Analisar os arquivos alterados nos commits para inferir sistemas:

| Arquivo alterado                   | Sistema               |
| ---------------------------------- | --------------------- |
| `Dockerfile`, `nginx*`, `scripts/` | Imagem Docker / nginx |
| `package.json`, `yarn.lock`        | Dependências frontend |
| `src/`                             | Aplicação frontend    |
| `.gitlab-ci.yml`                   | Pipeline de CD        |
| `docs/security/`                   | Segurança / CVEs      |
| `src/services/`                    | Integrações de API    |

### 4. Inferir riscos

- Mudanças em `Dockerfile` → risco de regressão na configuração nginx/CSP
- Upgrade de dependências → risco de incompatibilidade de API
- Mudanças em `src/utils/authorize.ts` ou fluxo de autenticação → risco alto, citar explicitamente
- Mudanças em `src/services/` → risco de regressão em chamadas de API

### 5. Determinar evidências

- Verificar se existe `scripts/test-*.sh` → incluir como evidência de testes locais
- Verificar resultado de testes Jest/Cypress na descrição dos MRs
- Verificar documentação em `docs/security/` para CVEs

### 6. Gerar o arquivo

- **Destino:** `docs/change_requests/YYYY-MM-DD_post-<TAG-BASE>.md`
- **Data:** data atual (hoje)
- Preencher o template em [templates/cr-template.md](templates/cr-template.md)
- Seções sem informação disponível: preencher com `N/A`

## Regras

- Sempre consolidar todos os MRs do período em **um único arquivo**
- Nomear o arquivo com a data de criação da CR (não a data dos commits)
- Padrão de nome: `YYYY-MM-DD_post-<TAG-BASE>.md` (ex: `2026-04-15_post-1.29.0.md`)
- Incluir a URL completa de cada MR nos passos de execução
- O rollback é sempre: revert dos commits + execução da pipeline
- Não inventar dados — usar `N/A` para campos sem informação concreta

## Anti-patterns

- ❌ Criar uma CR por commit (consolidar tudo em um arquivo)
- ❌ Inventar URLs de MRs — sempre buscar via GitLab API
- ❌ Omitir o rollback
- ❌ Deixar campos obrigatórios em branco — usar `N/A` se não houver dado
- ❌ Criar o arquivo fora de `docs/change_requests/`

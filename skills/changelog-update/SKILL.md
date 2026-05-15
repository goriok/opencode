---
name: changelog-update
description: Atualiza o CHANGELOG.md do projeto idmagalu-front com entradas novas, seguindo o padrão atual do arquivo (Era 1). Invocar quando o usuário pedir para atualizar, registrar ou documentar mudanças no CHANGELOG.
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Bash
tool: opencode-only
---

# Changelog Update

Insere entradas novas no `CHANGELOG.md` seguindo o padrão atual do projeto.

## Padrão atual do projeto (Era 1 — versão 1.28.x em diante)

### Cabeçalho de versão

```markdown
## [1.30.0](https://gitlab.luizalabs.com/luizalabs/autoseg/front/idmagalu/compare/1.29.0...1.30.0) (YYYY-MM-DD)
```

- Nível `##` (H2) — **não usar `#` (H1)**, mesmo que `1.29.0` esteja com `#` no arquivo atual (anomalia isolada)
- URL no formato `…/compare/<anterior>...<nova>`
- Data no formato `(YYYY-MM-DD)`

### Bloco "Unreleased" (antes de uma nova tag)

Quando ainda não há tag para o conjunto de mudanças:

```markdown
## [Unreleased] — pós-release <TAG-BASE> (YYYY-MM-DD)
```

- Data = data dos commits ou data de escrita da entrada
- Separar do próximo bloco com `---` em linha própria

### Categorias aceitas

Usar somente as categorias abaixo, nesta ordem de preferência:

| Categoria              | Quando usar                                                                      |
| ---------------------- | -------------------------------------------------------------------------------- |
| `### Features`         | Funcionalidade nova para o usuário final                                         |
| `### Bug Fixes`        | Correção de bug                                                                  |
| `### Improvements`     | Melhoria em algo existente (performance, UX, deps)                               |
| `### Chores`           | Tarefa técnica sem impacto direto no usuário (CI, Dockerfile, deps de segurança) |
| `### Code Refactoring` | Refatoração sem mudança de comportamento                                         |
| `### Documentation`    | Mudanças apenas em docs                                                          |
| `### Test`             | Cobertura de testes                                                              |

- Sempre plural e com `###` (H3)
- **Nunca** usar `## Fix`, `## Added`, `### Fixed`, `### Refactor`, `### Added` — são padrões de eras anteriores e não devem ser propagados

### Formato de item

```markdown
- <descrição concisa da mudança> ([!<iid>](url-mr))
```

- Marcador: **hífen** `-` (não asterisco)
- Link de MR **inline no final**, entre parênteses: `([!1148](url))`
- Se o item vier de um commit sem MR, usar SHA de 7 chars: `([abc1234](url-commit))`
- Descrições em **português**

## Passos de execução

### 1. Ler o CHANGELOG atual

```bash
# Verificar o topo do arquivo para entender o contexto atual
head -30 CHANGELOG.md
```

### 2. Identificar as mudanças a registrar

- Se vier de uma CR (`docs/change_requests/`): extrair título, categoria e MRs de lá
- Se vier de commits: `git log <TAG>..HEAD --format="%H %s" --no-merges`
- Se o usuário descrever manualmente: usar a descrição fornecida

### 3. Mapear categoria

| Tipo de mudança                          | Categoria              |
| ---------------------------------------- | ---------------------- |
| Nova funcionalidade                      | `### Features`         |
| Correção de bug                          | `### Bug Fixes`        |
| Upgrade de dep / melhoria de UX          | `### Improvements`     |
| Dockerfile, CI, nginx, segurança         | `### Chores`           |
| Refatoração sem mudança de comportamento | `### Code Refactoring` |
| Documentação                             | `### Documentation`    |
| Testes                                   | `### Test`             |

### 4. Decidir onde inserir

- **Nova versão tagueada:** inserir novo bloco `## [X.Y.Z](url) (data)` acima da versão anterior mais recente — logo após o `# Changelog`
- **Mudanças não tagueadas:** usar ou atualizar bloco `## [Unreleased]` logo após o `# Changelog`
- **Adicionar item a versão existente:** localizar a versão e a categoria correta, inserir o item na lista

### 5. Inserir a entrada

Usar o template em [templates/entry.md](templates/entry.md) como referência.

## Regras

- Sempre inserir novas entradas no **topo** do arquivo, logo após `# Changelog`
- Nunca remover ou alterar entradas já existentes
- Nunca corrigir inconsistências de versões antigas — registrar apenas o novo
- Separar bloco `[Unreleased]` do próximo bloco com `---`
- Não inventar URLs de MR — buscar via GitLab API ou checar na CR/commit

## Anti-patterns

- ❌ Criar seção com `## Fix` ou `## Added` (H2 — padrão legado)
- ❌ Usar `### Fixed`, `### Refactor`, `### Added` (padrão legado)
- ❌ Usar asterisco `*` como marcador de item
- ❌ Colocar link de MR solto em linha separada abaixo do item
- ❌ Inserir entrada no meio do arquivo — sempre no topo
- ❌ Usar SHA de commit quando há MR disponível

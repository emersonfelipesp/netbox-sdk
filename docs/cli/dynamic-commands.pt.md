# Comandos dinâmicos

Todo recurso NetBox alcançável pela API é registrado automaticamente como subcomando Typer, derivado do esquema OpenAPI integrado no momento da importação. Isso significa que `--help` funciona em todos os níveis e o completion do shell é totalmente suportado.

---

## Estrutura do comando

```
nbx <group> <resource> <action> [options]
```

Por exemplo:

```bash
nbx dcim devices list
nbx dcim devices get --id 1
nbx ipam prefixes create --body-json '{...}' --confirm
```

---

## Descoberta

Use os comandos de descoberta para explorar o que está disponível:

```bash
# Todos os grupos de app
nbx groups
# → circuits, core, dcim, extras, ipam, plugins, tenancy, users, virtualization, vpn, wireless

# Recursos em um grupo
nbx resources dcim
# → cable-terminations, cables, console-ports, device-bays, device-roles, devices, …

# Incluir recursos de plugins / objetos customizados da instância NetBox configurada
nbx resources plugins --live

# Ajuda em qualquer nível
nbx dcim --help
nbx dcim devices --help
nbx dcim devices list --help
```

---

## Ações

| Ação | Método HTTP | Caminho | Notas |
|--------|------------|------|-------|
| `list` | `GET` | `/api/<group>/<resource>/` | Retorna lista paginada; suporta `--all` |
| `get` | `GET` | `/api/<group>/<resource>/{id}/` | Requer `--id` |
| `create` | `POST` | `/api/<group>/<resource>/` | Requer `--body-json` ou `--body-file` |
| `update` | `PUT` | `/api/<group>/<resource>/{id}/` | Requer `--id` e corpo |
| `patch` | `PATCH` | `/api/<group>/<resource>/{id}/` | Requer `--id` e corpo |
| `delete` | `DELETE` | `/api/<group>/<resource>/{id}/` | Requer `--id` |
| `bulk-update` | `PUT` | `/api/<group>/<resource>/` | Corpo em array; sem `--id`; caminho de lista |
| `bulk-patch` | `PATCH` | `/api/<group>/<resource>/` | Corpo em array; sem `--id`; caminho de lista |
| `bulk-delete` | `DELETE` | `/api/<group>/<resource>/` | Corpo em array; sem `--id`; caminho de lista |
| `filters` | — | somente local | Exibe parâmetros de filtro disponíveis do esquema |

Nem todo recurso suporta todas as ações — a disponibilidade depende do esquema OpenAPI.

---

## Opções (todas as ações)

| Flag | Descrição |
|------|-------------|
| `--netbox-version` / `--api-version` | Opção global para forçar uma linha de esquema integrada suportada (`4.3`, `4.4`, `4.5`, `4.6`, `4.7`) |
| `--id INTEGER` | ID do objeto para operações de detalhe (`get`, `update`, `patch`, `delete`) |
| `-q` / `--query KEY=VALUE` | Filtro de query string (repetível) |
| `-H` / `--header HEADER=VALUE` | Cabeçalho HTTP da requisição; `Header: Value` também é aceito (repetível) |
| `--body-json TEXT` | Corpo JSON inline da requisição |
| `--body-file PATH` | Caminho para arquivo JSON do corpo |
| `--all` | Paginação automática: segue links `next` e retorna todos os registros (só `list`) |
| `--max-records INTEGER` | Limite superior para `--all` (padrão: 10 000) |
| `--json` | Saída JSON bruta |
| `--yaml` | Saída YAML |
| `--markdown` | Saída Markdown com tabelas primeiro |
| `--trace` | Buscar e renderizar trace de cabo ASCII (apenas interfaces, só `get`) |
| `--select TEXT` | Caminho JSON com ponto para extrair campo da resposta (ex.: `results.0.name`) |
| `--columns TEXT` | Lista separada por vírgulas de colunas na saída tabular |
| `--max-columns INTEGER` | Número máximo de colunas (padrão: 6) |
| `--dry-run` | Pré-visualizar escrita create/update/patch/delete/em lote sem executar |
| `--confirm` | Confirmar uma escrita real create/update/patch/delete/em lote |

`--json`, `--yaml` e `--markdown` são mutuamente exclusivos.

---

## Seleção de versão do NetBox

`nbx` suporta em paralelo todas as superfícies de comando integradas (`4.3`, `4.4`, `4.5`, `4.6` e `4.7`):

- Por padrão, a árvore estática de comandos usa o schema oficial GA integrado do NetBox 4.7.
- Durante a execução de comandos, auxiliares de descoberta e abertura de TUI, `nbx` verifica a versão da instância configurada e usa o esquema integrado correspondente quando a linha é suportada.
- Se a instância configurada não puder ser alcançada, se a detecção de versão falhar ou se o schema ao vivo for inválido, a execução falha de forma segura em vez de substituir o contrato integrado padrão.
- As visualizações `--dry-run`, que não criam cliente, usam o schema explícito/estático que registrou o comando e nunca consultam a instância.
- Use `--netbox-version` / `--api-version` ou `NETBOX_SDK_NETBOX_VERSION` para fixar explicitamente o esquema integrado.

```bash
# Descoberta de comandos padrão em 4.7
nbx dcim cable-bundles list --help

# Fixar descoberta e execução em NetBox 4.5
nbx --netbox-version 4.5 dcim devices list
NETBOX_SDK_NETBOX_VERSION=4.5 nbx resources dcim
```

Versões patch são normalizadas para a linha de release: `4.5.10` usa `4.5`, e `4.6.2` usa `4.6`.

---

## Filtragem

A flag `-q` / `--query` mapeia para parâmetros de query da API NetBox:

```bash
nbx dcim devices list -q site=nyc01
nbx dcim devices list -q status=active -q role=spine
nbx ipam prefixes list -q family=6 -q status=active
nbx dcim interfaces list -q device_id=1
nbx extras tags list -q tag=prod -q tag=edge
```

Várias flags `-q` são combinadas com AND. Repetir a mesma chave preserva parâmetros de query repetidos, usados pelo NetBox em filtros como múltiplas tags.

---

## Cabeçalhos HTTP

Use `-H` / `--header` em comandos dinâmicos, `nbx call` e `nbx dev http` quando a interação com a API precisar de cabeçalhos condicionais como `If-Match` ou cabeçalhos customizados:

```bash
nbx dcim devices patch --id 42 -H 'If-Match: "etag-value"' --body-json '{"status":"active"}' --confirm
nbx call PATCH /api/dcim/devices/42/ -H 'If-Match: "etag-value"' --body-json '{"status":"active"}' --confirm
nbx dev http get --path /api/dcim/devices/ -H 'Accept: application/json'
```

---

## Descoberta de filtros (`filters`)

A ação `filters` exibe os parâmetros de query disponíveis para um recurso diretamente do esquema integrado — sem nenhuma requisição HTTP:

```bash
nbx dcim devices filters
nbx extras tags filters
nbx ipam prefixes filters
```

Exemplo de saída para `extras tags`:

```
Filter parameters for extras/tags:

  q          (string)  — Search
  color      (string)
  id         (integer)
  name       (string)
  slug       (string)
```

Use isso para descobrir quais chaves `-q` são válidas antes de executar um `list` filtrado.

---

## Paginação automática (`--all`)

Por padrão, `list` retorna uma página (até o tamanho de página do servidor NetBox, geralmente 50 registros). Use `--all` para seguir todos os links `next` e receber uma resposta sintetizada contendo todos os registros correspondentes:

```bash
# Buscar todos os dispositivos independente do tamanho de página
nbx dcim devices list --all

# Limitar a 200 registros entre todas as páginas
nbx dcim devices list --all --max-records 200

# Combinar com filtros
nbx dcim devices list --all -q status=active --json
```

`--max-records` padrão é 10 000. Quando a contagem acumulada atingir o limite, a paginação para e o resultado parcial é retornado.
Alvos de página repetidos, valores `results` malformados e páginas que fornecem
outro link `next` sem adicionar registros falham com `PaginationError`, em vez
de repetir indefinidamente.

---

## Operações em lote

Operações em lote apontam para o caminho de lista com corpo em array — `--id` não é necessário nem aceito.

```bash
# Bulk-patch: atualização parcial de vários objetos
nbx extras tags bulk-patch --body-json '[{"id":1,"color":"aa1409"},{"id":2,"color":"0c7a00"}]' --confirm

# Bulk-update: substituição completa de vários objetos (todos os campos obrigatórios devem estar presentes)
nbx extras tags bulk-update --body-json '[{"id":1,"name":"tag-a","slug":"tag-a","color":"ff0000"}]' --confirm

# Bulk-delete: excluir vários objetos por id
nbx extras tags bulk-delete --body-json '[{"id":1},{"id":2}]' --confirm
```

Essas ações só são registradas para recursos onde o esquema OpenAPI expõe PUT/PATCH/DELETE no caminho de lista.

---

## Formatos de saída

=== "Tabela Rich (padrão)"

    ```bash
    nbx dcim devices list
    ```

    Renderiza uma tabela Rich com colunas priorizadas: `id`, `name`, `status`, `site`, `role`, `type`, etc.

=== "JSON"

    ```bash
    nbx dcim devices list --json
    ```

    Imprime a resposta paginada bruta da API como JSON indentado. Útil para encadear com `jq`.

=== "YAML"

    ```bash
    nbx dcim devices list --yaml
    ```

    Renderiza a resposta como YAML.

=== "Markdown"

    ```bash
    nbx dcim devices list --markdown
    ```

    Renderiza JSON da API como saída Markdown com tabelas primeiro.

---

## Seleção de campos (`--select`)

Extraia campos específicos da resposta JSON com notação de ponto:

```bash
# Obter o nome do primeiro dispositivo
nbx dcim devices list --select results.0.name
```

Apenas índices numéricos de lista são suportados em caminhos (sem curingas como `[*]`).

Padrões de caminho suportados:
- `results.0.name` — Acessa objeto aninhado em índice numérico
- `count` — Acessa campos de nível superior

---

## Controle de colunas (`--columns`, `--max-columns`)

Limite quais colunas aparecem na saída tabular:

```bash
# Exibir apenas colunas específicas
nbx dcim devices list --columns id,name,status

# Limitar o total de colunas a 3
nbx dcim devices list --max-columns 3

# Combinar ambos
nbx dcim devices list --columns id,name,status --max-columns 2
```

A flag `--columns` aceita uma lista separada por vírgulas de nomes de campo. A flag `--max-columns` limita o número total de colunas exibidas, padrão 6.

---

## Dry run (`--dry-run`)

Pré-visualize o que uma operação de escrita enviaria sem executá-la:

```bash
# Pré-visualizar create
nbx dcim devices create --dry-run --body-json '{"name":"test-device","site":1}'

# Pré-visualizar update
nbx dcim devices update --dry-run --id 1 --body-json '{"name":"updated-name"}'

# Pré-visualizar delete
nbx dcim devices delete --dry-run --id 1

# Pré-visualizar requisição explícita de plugin ausente do schema empacotado
nbx call POST /api/plugins/custom/widgets/ --dry-run --body-json '{"name":"widget-a"}'
```

A saída mostra método HTTP, caminho e corpo da requisição em uma tabela
formatada. Pré-visualizações com `nbx call` também mostram parâmetros de query
analisados e cabeçalhos não sensíveis. A flag `--dry-run` só é válida para
ações resolvidas como `POST`, `PUT`, `PATCH` ou `DELETE` (incluindo as ações
CRUD/em lote nomeadas e requisições `nbx call` com método de escrita).

Escritas reais são recusadas pela própria CLI em execução, salvo quando o
comando inclui `--confirm` ou o ambiente do processo contém
`NETBOX_SDK_CONFIRM_WRITE=1`. O gate vale para toda ação dinâmica resolvida
como `POST`, `PUT`, `PATCH` ou `DELETE`, inclusive uma ação escrita diretamente
como método HTTP, além de CRUD/sync Proxbox, `nbx call` e `nbx dev http` com
método de escrita e verbos mutáveis de `nbx branching`/`nbx branch`,
independentemente de `nbx` ser iniciado diretamente, por script ou
subprocesso.
`--dry-run` não requer confirmação porque não faz requisição HTTP.

---

## Trace de cabo

Para `dcim/interfaces`, a ação `get` suporta `--trace` para buscar e exibir o caminho do cabo como diagrama ASCII:

```bash
nbx dcim interfaces get --id 4 --trace
```

Saída:

```
Cable Trace:
┌────────────────────────────────────┐
│         dmi01-akron-rtr01          │
│       GigabitEthernet0/1/1         │
└────────────────────────────────────┘
                │
                │  Cable #36
                │  Connected
                │
┌────────────────────────────────────┐
│       GigabitEthernet1/0/2         │
│         dmi01-akron-sw01           │
└────────────────────────────────────┘

Trace Completed - 1 segment(s)
```

---

## Variante do perfil demo

A mesma árvore de comandos dinâmicos está registrada sob `nbx demo` e aponta para `demo.netbox.dev`:

```bash
nbx demo dcim devices list
nbx demo ipam prefixes list
nbx demo dcim interfaces get --id 4 --trace
```

Veja [Perfil demo](demo-profile.md) para a configuração.

---

## Como funciona

Na inicialização, `_register_openapi_subcommands()` em `dynamic.py` constrói um `SchemaIndex` sem rede a partir do esquema integrado selecionado por `--netbox-version` / `NETBOX_SDK_NETBOX_VERSION`, com padrão NetBox 4.7. Em seguida, cria um sub-app Typer para cada grupo, um sub-app aninhado para cada recurso e um comando para cada ação suportada. O mesmo registro executa duas vezes — uma para o `app` raiz e outra para `demo_app` com a fábrica de cliente demo.

A execução real do comando usa `_get_runtime_index()` de `runtime.py`. Overrides explícitos de versão têm prioridade; caso contrário, a CLI consulta a instância configurada e seleciona o esquema integrado correspondente para linhas de release NetBox suportadas. Uma falha de detecção ou de schema em um perfil configurado é terminal; somente perfis sem URL base podem usar o contrato integrado padrão. As visualizações dry-run permanecem sem rede e são resolvidas pelo índice estático de registro.

Para recursos de plugins / objetos customizados, o esquema integrado dá ao `nbx` a árvore estática de comandos que ele conhece. Use `--live` com `groups`, `resources` ou `ops` para enriquecer esse índice a partir da instância NetBox configurada via `/api/plugins/` e `/api/core/object-types/`. Invocações dinâmicas livres também tentam enriquecimento ao vivo quando o recurso solicitado não existe no esquema integrado.

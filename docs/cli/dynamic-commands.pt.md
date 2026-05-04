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
nbx ipam prefixes create --body-json '{...}'
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
| `list` | `GET` | `/api/<group>/<resource>/` | Retorna lista paginada |
| `get` | `GET` | `/api/<group>/<resource>/{id}/` | Requer `--id` |
| `create` | `POST` | `/api/<group>/<resource>/` | Requer `--body-json` ou `--body-file` |
| `update` | `PUT` | `/api/<group>/<resource>/{id}/` | Requer `--id` e corpo |
| `patch` | `PATCH` | `/api/<group>/<resource>/{id}/` | Requer `--id` e corpo |
| `delete` | `DELETE` | `/api/<group>/<resource>/{id}/` | Requer `--id` |

Nem todo recurso suporta todas as ações — a disponibilidade depende do esquema OpenAPI.

---

## Opções (todas as ações)

| Flag | Descrição |
|------|-------------|
| `--id INTEGER` | ID do objeto para operações de detalhe (`get`, `update`, `patch`, `delete`) |
| `-q` / `--query KEY=VALUE` | Filtro de query string (repetível) |
| `--body-json TEXT` | Corpo JSON inline da requisição |
| `--body-file PATH` | Caminho para arquivo JSON do corpo |
| `--json` | Saída JSON bruta |
| `--yaml` | Saída YAML |
| `--markdown` | Saída Markdown com tabelas primeiro |
| `--trace` | Buscar e renderizar trace de cabo ASCII (apenas interfaces, só `get`) |
| `--select TEXT` | Caminho JSON com ponto para extrair campo da resposta (ex.: `results.0.name`) |
| `--columns TEXT` | Lista separada por vírgulas de colunas na saída tabular |
| `--max-columns INTEGER` | Número máximo de colunas (padrão: 6) |
| `--dry-run` | Pré-visualizar operação de escrita sem executar (só create/update/patch/delete) |

`--json`, `--yaml` e `--markdown` são mutuamente exclusivos.

---

## Filtragem

A flag `-q` / `--query` mapeia para parâmetros de query da API NetBox:

```bash
nbx dcim devices list -q site=nyc01
nbx dcim devices list -q status=active -q role=spine
nbx ipam prefixes list -q family=6 -q status=active
nbx dcim interfaces list -q device_id=1
```

Várias flags `-q` são combinadas com AND.

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
```

A saída mostra método HTTP, caminho e corpo da requisição em uma tabela formatada. A flag `--dry-run` só é válida para operações de escrita (`create`, `update`, `patch`, `delete`).

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

Na inicialização, `_register_openapi_subcommands()` em `cli.py` lê `reference/openapi/netbox-openapi.json`, constrói um `SchemaIndex`, depois cria um sub-app Typer para cada grupo, um sub-app aninhado para cada recurso e um comando para cada ação suportada. O mesmo registro executa duas vezes — uma para o `app` raiz e outra para `demo_app` com `_get_demo_client` como fábrica do cliente.

Para recursos de plugins / objetos customizados, o esquema integrado dá ao `nbx` a árvore estática de comandos que ele conhece. Use `--live` com `groups`, `resources` ou `ops` para enriquecer esse índice a partir da instância NetBox configurada via `/api/plugins/` e `/api/core/object-types/`. Invocações dinâmicas livres também tentam enriquecimento ao vivo quando o recurso solicitado não existe no esquema integrado.

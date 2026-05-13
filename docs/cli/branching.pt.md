# Branching

A CLI expõe um subapp Typer para todas as operações do plugin
[`netbox-branching`](https://github.com/netboxlabs/netbox-branching).

```bash
nbx branching --help
nbx branch --help   # alias
```

## Status e listagem

```bash
nbx branching status
nbx branching list [--status ready]
nbx branching show <id-ou-schema_id>
nbx branching models    # registro de modelos branchable
nbx branching events
nbx branching changes [--branch <schema_id>]
```

## Ciclo de vida

```bash
nbx branching create --name feature-x [--description ...]
nbx branching update <id|schema_id> [--name ...]
nbx branching delete <id|schema_id> [--yes]
nbx branching archive <id|schema_id>
```

## Ações

`sync`, `merge` e `revert` retornam jobs enfileirados. `--wait` faz polling
até o job terminar.

```bash
nbx branching sync   <id|schema_id> [--wait] [--acknowledge-conflicts]
nbx branching merge  <id|schema_id> [--wait] [--acknowledge-conflicts]
nbx branching revert <id|schema_id> [--wait]
```

Se o servidor retornar um corpo de conflitos, a CLI imprime uma tabela
estruturada e termina com status diferente de zero.

## Requisições no escopo de uma branch

A opção global `--branch` (também lê a variável de ambiente
`NETBOX_BRANCH`) envolve a invocação atual para que **todos** os comandos —
DCIM, IPAM, comandos dinâmicos OpenAPI etc. — enviem o header
`X-NetBox-Branch` durante o tempo de vida da chamada:

```bash
nbx --branch feature-x dcim devices list
NETBOX_BRANCH=feature-x nbx ipam prefixes list
```

O argumento resolve um `schema_id` ou um nome de branch para o `schema_id`
correspondente.

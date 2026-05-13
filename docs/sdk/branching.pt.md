# Branching

O NetBox 4.x pode hospedar o plugin
[`netbox-branching`](https://github.com/netboxlabs/netbox-branching), que dá a
cada alteração um fluxo de trabalho de branch, revisão e merge no estilo do
git. O SDK fornece um `BranchingClient` de alto nível e suporte nativo no
header para que CLI, SDK e TUI possam apontar para uma branch em uma única
chamada.

Instale o extra opcional para deixar essa dependência explícita:

```bash
pip install 'netbox-sdk[branching]'
```

O extra é um marcador — não adiciona dependências em tempo de execução — mas
fixá-lo documenta a intenção e permite que adicionemos helpers no futuro sem
quebrar instalações enxutas.

## Detecção de funcionalidade

```python
from netbox_sdk import api
from netbox_sdk.branching import BranchingClient

nb = api(base_url="https://netbox.example.com", token="…")
branching = BranchingClient(nb)

if not await branching.is_available():
    raise RuntimeError("netbox-branching não está instalado neste NetBox")
```

`is_available()` faz `GET /api/plugins/branching/` e retorna `True` quando o
plugin responde.

## CRUD

```python
branches = await branching.list()
branch   = await branching.get("td5smq0f")
branch   = await branching.create(name="feature-x")
await branching.update("td5smq0f", description="…")
await branching.delete("td5smq0f")
```

Todas as ações aceitam tanto o `id` numérico quanto o `schema_id` de 8
caracteres.

## Ações

`sync`, `merge` e `revert` retornam um `Job` enfileirado. Passe `wait=True`
para fazer polling em `/api/core/jobs/{id}/` até a conclusão.

```python
job = await branching.sync("td5smq0f", commit=True, wait=True)
job = await branching.merge("td5smq0f", commit=True, wait=True,
                            acknowledge_conflicts=False)
job = await branching.revert("td5smq0f", wait=True)
branch = await branching.archive("td5smq0f")
```

Se o servidor retornar `409` com um corpo de conflitos, o SDK levanta
`BranchConflictError(conflicts=…)`, expondo a lista de conflitos para que
quem chama possa renderizá-la.

## Ativando uma branch

O plugin escopa para uma branch toda requisição que carregue o header
`X-NetBox-Branch`. A fachada assíncrona expõe dois padrões:

```python
# Escopo local de contexto assíncrono — limpo automaticamente, seguro sob
# concorrência.
async with nb.activate_branch("td5smq0f"):
    devices = await nb.dcim.devices.list()

# Longa duração, aplicado a toda requisição até ser limpo.
nb.client.persistent_headers["X-NetBox-Branch"] = "td5smq0f"
```

`activate_branch()` aceita um `Branch`, um `schema_id` ou o nome de uma
branch (o SDK resolve o nome automaticamente).

## Coleções somente-leitura

```python
events  = await branching.events()           # /branch-events/
changes = await branching.changes()          # /changes/
models  = await branching.branchable_models()
```

## Clientes tipados

A mesma superfície está disponível pelo cliente tipado por versão:

```python
from netbox_sdk import typed_api

nb = typed_api("4.6", base_url="…", token="…")
branches = await nb.plugins.branching.branches.list()
```

`PluginsApp.branching` está conectado para NetBox 4.4, 4.5 e 4.6.

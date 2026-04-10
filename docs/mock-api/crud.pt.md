# Operações CRUD

O servidor mock suporta o ciclo de vida CRUD completo do NetBox: criar, ler, atualizar e deletar. Esta página demonstra cada operação usando `fastapi.testclient.TestClient`.

## Configuração

```python
from fastapi.testclient import TestClient
from netbox_sdk.mock import create_mock_app

app = create_mock_app()
client = TestClient(app)
```

Para testes que precisam de um estado limpo antes de cada execução, chame o endpoint de reset:

```python
client.post("/mock/reset")
```

## Criar (POST)

`POST` em um endpoint de lista retorna o objeto criado com um `id` inteiro atribuído automaticamente e status `201`.

```python
resp = client.post(
    "/api/dcim/sites/",
    json={"name": "London HQ", "slug": "london-hq"},
)
assert resp.status_code == 201
site = resp.json()
print(site["id"])    # inteiro atribuído automaticamente
print(site["name"])  # "London HQ"
```

Os IDs são por coleção e sempre crescentes de forma monotônica.

## Ler (GET)

### Listar todos os objetos

```python
resp = client.get("/api/dcim/sites/")
assert resp.status_code == 200
body = resp.json()
print(body["count"])    # total de objetos correspondentes
print(body["results"])  # lista de objetos
```

Todas as respostas de lista usam o envelope de paginação do NetBox:

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [...]
}
```

### Obter um único objeto

```python
resp = client.get(f"/api/dcim/sites/{site_id}/")
assert resp.status_code == 200
print(resp.json()["name"])
```

### Auto-seed de IDs desconhecidos

Buscar um ID que nunca foi criado retorna um stub gerado deterministicamente em vez de 404:

```python
resp = client.get("/api/dcim/sites/9999/")
assert resp.status_code == 200  # auto-seed
assert resp.json()["id"] == 9999
```

Isso é útil ao testar código que segue IDs de chave estrangeira aninhada retornados por outros endpoints.

## Atualizar (PUT / PATCH)

### Substituição completa (PUT)

```python
resp = client.put(
    f"/api/dcim/sites/{site_id}/",
    json={"name": "Nome Atualizado", "slug": "nome-atualizado"},
)
assert resp.status_code == 200
assert resp.json()["name"] == "Nome Atualizado"
```

### Atualização parcial (PATCH)

```python
resp = client.patch(
    f"/api/dcim/sites/{site_id}/",
    json={"name": "Nome Corrigido"},
)
assert resp.status_code == 200
assert resp.json()["name"] == "Nome Corrigido"
```

O PATCH mescla os campos fornecidos no objeto existente — campos omitidos mantêm seus valores atuais.

## Deletar (DELETE)

```python
resp = client.delete(f"/api/dcim/sites/{site_id}/")
assert resp.status_code == 204
```

Após a exclusão, requisições GET para o mesmo URL retornam 404:

```python
resp = client.get(f"/api/dcim/sites/{site_id}/")
assert resp.status_code == 404
```

## Exemplo completo do ciclo de vida

```python
from fastapi.testclient import TestClient
from netbox_sdk.mock import create_mock_app

app = create_mock_app()

with TestClient(app) as client:
    client.post("/mock/reset")

    # Criar
    site = client.post(
        "/api/dcim/sites/",
        json={"name": "Site de Teste", "slug": "site-de-teste"},
    ).json()
    site_id = site["id"]

    # Ler
    assert client.get(f"/api/dcim/sites/{site_id}/").json()["name"] == "Site de Teste"
    assert client.get("/api/dcim/sites/").json()["count"] == 1

    # Atualizar
    client.patch(f"/api/dcim/sites/{site_id}/", json={"name": "Renomeado"})
    assert client.get(f"/api/dcim/sites/{site_id}/").json()["name"] == "Renomeado"

    # Deletar
    assert client.delete(f"/api/dcim/sites/{site_id}/").status_code == 204
    assert client.get(f"/api/dcim/sites/{site_id}/").status_code == 404
    assert client.get("/api/dcim/sites/").json()["count"] == 0
```

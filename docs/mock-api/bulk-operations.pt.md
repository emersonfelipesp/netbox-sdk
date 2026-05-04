# Operações em Lote

Os endpoints de lista do NetBox aceitam arrays nos corpos das requisições para POST, PUT, PATCH e DELETE — permitindo que múltiplos objetos sejam criados, atualizados ou excluídos em uma única requisição. O servidor mock implementa todas as quatro operações em lote.

## Criação em lote (POST com array)

Passe um array JSON para qualquer endpoint de lista. A resposta é uma lista de objetos criados com IDs atribuídos automaticamente.

```python
from fastapi.testclient import TestClient
from netbox_sdk.mock import create_mock_app

app = create_mock_app()
client = TestClient(app)
client.post("/mock/reset")

resp = client.post(
    "/api/ipam/vlans/",
    json=[
        {"name": "Gerenciamento", "vid": 1},
        {"name": "Produção", "vid": 100},
        {"name": "DMZ", "vid": 200},
    ],
)
assert resp.status_code == 201
vlans = resp.json()
assert isinstance(vlans, list)
assert len(vlans) == 3

vlan_ids = [v["id"] for v in vlans]
```

A contagem da lista reflete todos os objetos criados:

```python
assert client.get("/api/ipam/vlans/").json()["count"] == 3
```

## Atualização em lote (PUT com array)

Passe um array onde cada item inclui seu campo `id`. Todos os objetos listados são completamente substituídos.

```python
resp = client.put(
    "/api/ipam/vlans/",
    json=[
        {"id": vlan_ids[0], "name": "MGMT", "vid": 1},
        {"id": vlan_ids[1], "name": "PROD", "vid": 100},
    ],
)
assert resp.status_code == 200
updated = resp.json()
assert updated[0]["name"] == "MGMT"
assert updated[1]["name"] == "PROD"
```

## Atualização parcial em lote (PATCH com array)

Cada item deve incluir seu `id`. Somente os campos fornecidos são atualizados.

```python
resp = client.patch(
    "/api/ipam/vlans/",
    json=[
        {"id": vlan_ids[2], "name": "DMZ-Atualizado"},
    ],
)
assert resp.status_code == 200
assert resp.json()[0]["name"] == "DMZ-Atualizado"
```

## Exclusão em lote (DELETE com array)

!!! nota
    Use `client.request("DELETE", path, json=[...])` — o método `client.delete()` do Starlette não aceita o parâmetro `json`.

```python
resp = client.request(
    "DELETE",
    "/api/ipam/vlans/",
    json=[{"id": vlan_ids[0]}, {"id": vlan_ids[1]}],
)
assert resp.status_code == 204
```

Após a exclusão em lote, apenas os objetos não excluídos permanecem:

```python
assert client.get("/api/ipam/vlans/").json()["count"] == 1
```

## Detecção de único vs lote

O mesmo endpoint trata tanto objetos individuais quanto arrays. Não é necessária uma URL separada:

| Corpo da requisição | Comportamento | Resposta |
|---|---|---|
| `{"name": "x", "vid": 1}` | Criação única | Objeto único, 201 |
| `[{"name": "x", "vid": 1}, ...]` | Criação em lote | Array de objetos, 201 |
| `{"id": 1, "name": "y"}` | PUT/PATCH único | Objeto único, 200 |
| `[{"id": 1, "name": "y"}, ...]` | PUT/PATCH em lote | Array de objetos, 200 |
| _(sem corpo)_ | DELETE único | Vazio, 204 |
| `[{"id": 1}, {"id": 2}]` | DELETE em lote | Vazio, 204 |

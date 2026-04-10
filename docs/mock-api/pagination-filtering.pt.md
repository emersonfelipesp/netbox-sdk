# Paginação e Filtragem

O servidor mock retorna respostas de lista paginadas no estilo NetBox e suporta filtragem por parâmetros de consulta em qualquer campo.

## Envelope de paginação

Toda resposta de lista envolve os resultados no envelope padrão do NetBox:

```json
{
  "count": 50,
  "next": "http://testserver/api/dcim/sites/?limit=10&offset=10",
  "previous": null,
  "results": [...]
}
```

| Campo | Descrição |
|---|---|
| `count` | Número total de objetos correspondentes (em todas as páginas) |
| `next` | URL da próxima página, ou `null` na última página |
| `previous` | URL da página anterior, ou `null` na primeira página |
| `results` | Objetos na janela da página atual |

## Limit e offset

Use os parâmetros de consulta `limit` e `offset` para paginar pelos resultados:

```python
from fastapi.testclient import TestClient
from netbox_sdk.mock import create_mock_app

app = create_mock_app()
client = TestClient(app)
client.post("/mock/reset")

# Criar 10 sites
client.post(
    "/api/dcim/sites/",
    json=[{"name": f"Site-{i}", "slug": f"site-{i}"} for i in range(10)],
)

# Primeira página
resp = client.get("/api/dcim/sites/?limit=4&offset=0")
data = resp.json()
assert data["count"] == 10
assert len(data["results"]) == 4
assert data["next"] is not None
assert data["previous"] is None

# Segunda página
resp = client.get("/api/dcim/sites/?limit=4&offset=4")
data = resp.json()
assert len(data["results"]) == 4
assert data["next"] is not None
assert data["previous"] is not None

# Última página
resp = client.get("/api/dcim/sites/?limit=4&offset=8")
data = resp.json()
assert len(data["results"]) == 2
assert data["next"] is None
assert data["previous"] is not None
```

Quando `limit` não é especificado, todos os resultados são retornados em uma única página.

## Filtragem por parâmetros de consulta

Passe qualquer nome de campo como parâmetro de consulta para filtrar resultados. O filtro realiza uma correspondência de igualdade sensível a maiúsculas e minúsculas em campos string.

```python
client.post(
    "/api/dcim/sites/",
    json=[
        {"name": "Alpha", "slug": "alpha"},
        {"name": "Beta", "slug": "beta"},
        {"name": "Gamma", "slug": "gamma"},
    ],
)

# Filtrar por nome
resp = client.get("/api/dcim/sites/?name=Alpha")
assert resp.json()["count"] == 1
assert resp.json()["results"][0]["name"] == "Alpha"

# Sem correspondências
resp = client.get("/api/dcim/sites/?name=NaoExiste")
assert resp.json()["count"] == 0
assert resp.json()["results"] == []
```

## Combinando paginação e filtragem

Filtragem e paginação funcionam juntas. `count` reflete o total filtrado:

```python
# Criar 6 VLANs com nomes alternados
client.post(
    "/api/ipam/vlans/",
    json=[
        {"name": "MGMT", "vid": i * 10} for i in range(3)
    ] + [
        {"name": "PROD", "vid": 100 + i * 10} for i in range(3)
    ],
)

resp = client.get("/api/ipam/vlans/?name=MGMT&limit=2")
data = resp.json()
assert data["count"] == 3         # 3 VLANs MGMT no total
assert len(data["results"]) == 2  # 2 por página
```

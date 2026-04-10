# Servidor Standalone

O servidor mock pode ser executado como um serviço HTTP autônomo usando o uvicorn. Isso é útil para exploração manual da API, integração com clientes não-Python e desenvolvimento local contra a API do NetBox sem uma instância real.

## Instalação

O servidor standalone requer o uvicorn. Instale o extra `mock`:

```bash
pip install 'netbox-sdk[mock]'
```

## Iniciando o servidor

```bash
nbx-mock
```

O servidor inicia em `http://0.0.0.0:8001` por padrão e registra todas as requisições no console.

### Variáveis de ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `NETBOX_MOCK_VERSION` | `4.5` | Versão do OpenAPI do NetBox para gerar rotas |
| `NETBOX_MOCK_HOST` | `0.0.0.0` | Endereço de bind |
| `NETBOX_MOCK_PORT` | `8001` | Porta de escuta |
| `NETBOX_MOCK_DATA_PATH` | _(não definido)_ | Caminho para um arquivo JSON ou YAML com dados iniciais |

Exemplo:

```bash
NETBOX_MOCK_VERSION=4.3 NETBOX_MOCK_PORT=9000 nbx-mock
```

## Explorando a API

Uma vez em execução, a documentação interativa da API está disponível em:

- Swagger UI: `http://localhost:8001/docs`
- ReDoc: `http://localhost:8001/redoc`

Todos os ~1100 endpoints do NetBox são listados e executáveis pelo navegador.

## Usando com curl

```bash
# Criar um site
curl -s -X POST http://localhost:8001/api/dcim/sites/ \
  -H "Content-Type: application/json" \
  -d '{"name": "London HQ", "slug": "london-hq"}' | python3 -m json.tool

# Listar sites
curl -s http://localhost:8001/api/dcim/sites/ | python3 -m json.tool

# Obter um site específico (substitua 1 pelo id retornado)
curl -s http://localhost:8001/api/dcim/sites/1/ | python3 -m json.tool

# Atualizar um site
curl -s -X PATCH http://localhost:8001/api/dcim/sites/1/ \
  -H "Content-Type: application/json" \
  -d '{"name": "London DC"}' | python3 -m json.tool

# Deletar um site
curl -s -X DELETE http://localhost:8001/api/dcim/sites/1/ -v

# Resetar todo o estado
curl -s -X POST http://localhost:8001/mock/reset

# Verificar a saúde do servidor
curl -s http://localhost:8001/health
```

## Usando com o SDK NetBox

Aponte o `NetBoxApiClient` para o servidor mock:

```python
import asyncio
from netbox_sdk.client import NetBoxApiClient
from netbox_sdk.config import NetBoxConfig


async def main() -> None:
    config = NetBoxConfig(
        url="http://localhost:8001",
        token="mock-token",  # qualquer string é aceita
    )
    client = NetBoxApiClient(config)

    resp = await client.get("/api/dcim/sites/")
    data = await resp.json()
    print(f"Sites: {data['count']}")

    await client.close()


asyncio.run(main())
```

## Inicialização programática

Use `create_mock_app()` com o uvicorn diretamente em Python:

```python
import uvicorn
from netbox_sdk.mock import create_mock_app

app = create_mock_app(version="4.5")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")
```

## Dados iniciais

Pré-popule o servidor com dados fornecendo um arquivo JSON:

```json
{
  "/api/dcim/sites/": [
    {"name": "London HQ", "slug": "london-hq"},
    {"name": "New York DC", "slug": "new-york-dc"}
  ],
  "/api/ipam/vlans/": [
    {"name": "Gerenciamento", "vid": 1},
    {"name": "Produção", "vid": 100}
  ]
}
```

Em seguida, inicie o servidor com:

```bash
NETBOX_MOCK_DATA_PATH=/caminho/para/seed.json nbx-mock
```

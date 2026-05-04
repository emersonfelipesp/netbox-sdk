# API Mock

`netbox_sdk.mock` é um servidor FastAPI autossuficiente que gera dinamicamente todos os endpoints da API REST do NetBox a partir das especificações OpenAPI embutidas. Cada rota é sustentada por um armazenamento em memória, permitindo fluxos CRUD completos sem uma instância real do NetBox.

## Casos de uso

- Desenvolvimento do SDK sem conexão à internet
- Suítes de testes em CI que não precisam de um container NetBox real
- Testes de integração com reset de estado rápido e determinístico
- Exemplos, demonstrações e tutoriais

## Instalação

O servidor mock depende do FastAPI e, opcionalmente, do uvicorn (para uso standalone). Instale o extra `mock`:

```bash
pip install 'netbox-sdk[mock]'
```

Ou para desenvolvimento com o ambiente completo:

```bash
uv sync --dev --extra mock
```

## Início rápido

```python
from fastapi.testclient import TestClient
from netbox_sdk.mock import create_mock_app

app = create_mock_app()
client = TestClient(app)

# Criar um site
resp = client.post("/api/dcim/sites/", json={"name": "London HQ", "slug": "london-hq"})
assert resp.status_code == 201
site_id = resp.json()["id"]

# Buscar novamente
resp = client.get(f"/api/dcim/sites/{site_id}/")
assert resp.json()["name"] == "London HQ"

# Deletar
resp = client.delete(f"/api/dcim/sites/{site_id}/")
assert resp.status_code == 204
```

## Módulos

| Módulo | Responsabilidade |
|---|---|
| `netbox_sdk.mock.app` | Fábrica `create_mock_app()`, rotas utilitárias, montagem do app |
| `netbox_sdk.mock.routes` | Registro dinâmico de rotas a partir da especificação OpenAPI |
| `netbox_sdk.mock.state` | Armazenamento CRUD em memória `ThreadSafeMockStore` |
| `netbox_sdk.mock.schema_helpers` | Resolução de `$ref`, geração de valores de exemplo |
| `netbox_sdk.mock.netbox_fields` | Geradores de valores semânticos específicos do NetBox |
| `netbox_sdk.mock.loader` | Carregamento de dados mock customizados em JSON/YAML |

## Endpoints utilitários

Além de todos os caminhos da API NetBox, o servidor mock expõe:

| Endpoint | Método | Descrição |
|---|---|---|
| `/health` | `GET` | Retorna `{"status": "ready"}` |
| `/api/status/` | `GET` | Status mock do NetBox com informações de versão |
| `/mock/reset` | `POST` | Limpa todo o estado em memória |
| `/mock/state` | `GET` | Informa contagem de rotas e estatísticas do armazenamento |

## Versão do NetBox

O servidor mock usa por padrão a versão mais recente suportada do NetBox. Substitua com:

```bash
NETBOX_MOCK_VERSION=4.3 python seu_script.py
```

Ou passe a versão diretamente:

```python
app = create_mock_app(version="4.3")
```

Valores suportados: `4.3`, `4.4`, `4.5`, `4.6`.

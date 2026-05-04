# Integração com pytest

O servidor mock foi projetado para se integrar naturalmente com o pytest. Esta página cobre os padrões de fixture recomendados para testes isolados e repetíveis.

## Padrão básico de fixture

Crie o app uma vez no escopo do módulo para maior eficiência, depois redefina o estado antes de cada teste:

```python
import pytest
from fastapi.testclient import TestClient
from netbox_sdk.mock import create_mock_app


@pytest.fixture(scope="module")
def app():
    return create_mock_app()


@pytest.fixture()
def client(app):
    with TestClient(app) as c:
        c.post("/mock/reset")
        yield c
```

O `scope="module"` no `app` significa que o servidor mock (incluindo suas ~1100 rotas e análise do schema) é inicializado uma vez por módulo de teste. A fixture `client` por teste chama `/mock/reset` antes de ceder, dando a cada teste um armazenamento fresco e vazio.

## Escrevendo testes

Com as fixtures acima, cada função de teste começa sem dados:

```python
def test_criar_e_listar(client):
    client.post("/api/dcim/sites/", json={"name": "London", "slug": "london"})
    assert client.get("/api/dcim/sites/").json()["count"] == 1


def test_começa_vazio(client):
    # Independente de test_criar_e_listar — reset foi chamado antes deste teste
    assert client.get("/api/dcim/sites/").json()["count"] == 0
```

## Posicionamento do conftest.py

Coloque fixtures compartilhadas em `conftest.py` para que estejam disponíveis em múltiplos módulos de teste:

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from netbox_sdk.mock import create_mock_app


@pytest.fixture(scope="session")
def mock_app():
    """App mock com escopo de sessão — inicializado uma vez para toda a execução de testes."""
    return create_mock_app()


@pytest.fixture()
def mock_client(mock_app):
    """Client por teste com estado limpo."""
    with TestClient(mock_app) as c:
        c.post("/mock/reset")
        yield c
```

## Fixtures específicas por versão

Use parametrize para executar os mesmos testes em múltiplas versões do NetBox:

```python
@pytest.fixture(params=["4.3", "4.4", "4.5", "4.6"])
def versioned_client(request):
    app = create_mock_app(version=request.param)
    with TestClient(app) as c:
        c.post("/mock/reset")
        yield c


def test_versao_status(versioned_client):
    resp = versioned_client.get("/api/status/")
    assert resp.json()["netbox-version"].startswith("4.")
```

## Combinando testes mock e reais

Use uma variável de ambiente para alternar entre o servidor mock e uma instância real do NetBox:

```python
import os
import pytest
from fastapi.testclient import TestClient
from netbox_sdk.mock import create_mock_app


def obter_client_de_teste():
    """Retorna um TestClient para o mock ou um wrapper apontando para o NetBox real."""
    if os.getenv("NETBOX_LIVE_TEST"):
        import httpx
        base_url = os.environ["NETBOX_URL"]
        token = os.environ["NETBOX_TOKEN"]
        return httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Token {token}"},
        )
    app = create_mock_app()
    return TestClient(app)


@pytest.fixture()
def client():
    c = obter_client_de_teste()
    if isinstance(c, TestClient):
        with c as tc:
            tc.post("/mock/reset")
            yield tc
    else:
        yield c
```

Defina `NETBOX_LIVE_TEST=1` com `NETBOX_URL` e `NETBOX_TOKEN` para executar contra uma instância real. Deixe-os sem definição para usar o mock.

## Marcando testes

Atribua testes ao marcador de suíte correto para que o CI possa roteá-los corretamente:

```python
import pytest

pytestmark = pytest.mark.suite_sdk


def test_mock_api(client):
    ...
```

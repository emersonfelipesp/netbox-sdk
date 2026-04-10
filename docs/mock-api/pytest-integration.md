# pytest Integration

The mock server is designed to integrate naturally with pytest. This page covers the recommended fixture patterns for isolated, repeatable tests.

## Basic fixture pattern

Create the app once at module scope for efficiency, then reset state before each test:

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

The `scope="module"` on `app` means the mock server (including its ~1100 routes and schema parse) is initialized once per test module. The per-test `client` fixture calls `/mock/reset` before yielding, giving each test a fresh, empty store.

## Writing tests

With the fixtures above, each test function starts with no data:

```python
def test_create_and_list(client):
    client.post("/api/dcim/sites/", json={"name": "London", "slug": "london"})
    assert client.get("/api/dcim/sites/").json()["count"] == 1


def test_starts_empty(client):
    # Independent of test_create_and_list — reset was called before this test
    assert client.get("/api/dcim/sites/").json()["count"] == 0
```

## conftest.py placement

Place shared fixtures in `conftest.py` so they are available across multiple test modules:

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from netbox_sdk.mock import create_mock_app


@pytest.fixture(scope="session")
def mock_app():
    """Session-scoped mock app — initialized once for the entire test run."""
    return create_mock_app()


@pytest.fixture()
def mock_client(mock_app):
    """Per-test client with a clean state."""
    with TestClient(mock_app) as c:
        c.post("/mock/reset")
        yield c
```

## Version-specific fixtures

Use parametrize to run the same tests against multiple NetBox versions:

```python
@pytest.fixture(params=["4.3", "4.4", "4.5"])
def versioned_client(request):
    app = create_mock_app(version=request.param)
    with TestClient(app) as c:
        c.post("/mock/reset")
        yield c


def test_status_version(versioned_client):
    resp = versioned_client.get("/api/status/")
    assert resp.json()["netbox-version"].startswith("4.")
```

## Mixing mock and live tests

Use an environment variable to switch between the mock server and a live NetBox instance:

```python
import os
import pytest
from fastapi.testclient import TestClient
from netbox_sdk.mock import create_mock_app


def get_test_client():
    """Return a TestClient for the mock or a wrapper pointing at live NetBox."""
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
    c = get_test_client()
    if isinstance(c, TestClient):
        with c as tc:
            tc.post("/mock/reset")
            yield tc
    else:
        yield c
```

Set `NETBOX_LIVE_TEST=1` with `NETBOX_URL` and `NETBOX_TOKEN` to run against a real instance. Leave them unset to use the mock.

## Marking tests

Assign tests to the right suite marker so CI can route them correctly:

```python
import pytest

pytestmark = pytest.mark.suite_sdk


def test_mock_api(client):
    ...
```

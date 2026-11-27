import jwt
import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient

from main import app
from src.config import container
from src.config.request_context import RequestContext, get_request_context

API = "/api/v1"

TEST_SECRET = "chave-de-teste-siglog-wms-32-bytes-minimo"


@pytest.fixture(autouse=True)
def estado_limpo():
    container.reset()
    yield
    container.reset()


@pytest.fixture
def token_teste(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", TEST_SECRET)

    return jwt.encode(
        {
            "sub": "usuario-teste",
            "empresa_id": "empresa-teste",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
        },
        TEST_SECRET,
        algorithm="HS256",
    )


@pytest.fixture
def client(token_teste):
    app.dependency_overrides[get_request_context] = lambda: RequestContext(
        usuario_id="66666666-6666-4666-8666-666666666666",
        empresa_id="11111111-1111-4111-8111-111111111111",
        perfil_id="33333333-3333-4333-8333-333333333333",
    )

    try:
        with TestClient(
            app,
            headers={"Authorization": f"Bearer {token_teste}"},
        ) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_request_context, None)


@pytest.fixture
def eventos():
    return container.publisher.events


# ---- helpers usados pelos testes de integração ----
def criar_produto(client, sku="SKU-1"):
    r = client.post(
        f"{API}/products",
        json={"sku": sku, "description": "Produto", "unit": "UN"},
    )
    assert r.status_code == 201, r.text
    return r.json()


def criar_endereco(client, code="A-01", capacity=1000):
    r = client.post(
        f"{API}/addresses",
        json={"code": code, "capacity": capacity},
    )
    assert r.status_code == 201, r.text
    return r.json()


def receber_e_conferir(client, sku="SKU-1", quantidade=100, contado=None):
    r = client.post(
        f"{API}/receipts",
        json={
            "cargoId": "CARGA-1",
            "invoiceNumber": "NF-1",
            "items": [
                {"productId": sku, "expectedQuantity": quantidade}
            ],
        },
    )
    assert r.status_code == 201, r.text
    receipt = r.json()

    r = client.post(
        f"{API}/receipts/{receipt['id']}/conference",
        json={
            "items": [
                {
                    "productId": sku,
                    "countedQuantity": quantidade if contado is None else contado,
                }
            ],
        },
    )
    assert r.status_code == 200, r.text
    return r.json()


def estoque_pronto(client, sku="SKU-1", quantidade=100, endereco="A-01"):
    """Produto cadastrado, recebido, conferido e guardado."""
    criar_produto(client, sku)
    criar_endereco(client, endereco)
    receber_e_conferir(client, sku, quantidade)

    r = client.post(
        f"{API}/allocations",
        json={
            "productId": sku,
            "addressCode": endereco,
            "quantity": quantidade,
        },
    )
    assert r.status_code == 201, r.text

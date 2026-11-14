import pytest
from fastapi.testclient import TestClient

from main import app
from src.config import container

API = "/api/v1"


@pytest.fixture(autouse=True)
def estado_limpo():
    container.reset()
    yield
    container.reset()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def eventos():
    return container.publisher.events


# ---- helpers usados pelos testes de integração ----
def criar_produto(client, sku="SKU-1"):
    r = client.post(f"{API}/products", json={"sku": sku, "description": "Produto", "unit": "UN"})
    assert r.status_code == 201, r.text
    return r.json()


def criar_endereco(client, code="A-01", capacity=1000):
    r = client.post(f"{API}/addresses", json={"code": code, "capacity": capacity})
    assert r.status_code == 201, r.text
    return r.json()


def receber_e_conferir(client, sku="SKU-1", quantidade=100, contado=None):
    r = client.post(f"{API}/receipts", json={
        "cargoId": "CARGA-1", "invoiceNumber": "NF-1",
        "items": [{"productId": sku, "expectedQuantity": quantidade}],
    })
    assert r.status_code == 201, r.text
    receipt = r.json()
    r = client.post(f"{API}/receipts/{receipt['id']}/conference", json={
        "items": [{"productId": sku, "countedQuantity": quantidade if contado is None else contado}],
    })
    assert r.status_code == 200, r.text
    return r.json()


def estoque_pronto(client, sku="SKU-1", quantidade=100, endereco="A-01"):
    """Produto cadastrado, recebido, conferido e guardado."""
    criar_produto(client, sku)
    criar_endereco(client, endereco)
    receber_e_conferir(client, sku, quantidade)
    r = client.post(f"{API}/allocations", json={
        "productId": sku, "addressCode": endereco, "quantity": quantidade})
    assert r.status_code == 201, r.text

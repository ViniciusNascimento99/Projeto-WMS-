import jwt
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from main import app


SECRET = "chave-de-teste-siglog-wms-32-bytes-minimo"
ROTA = "/api/v1/products/produto-inexistente"


import pytest


@pytest.fixture(autouse=True)
def configurar_jwt_secret(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", SECRET)



def gerar_token(claims=None, secret=SECRET):
    if claims is None:
        claims = {
            "sub": "usuario-teste",
            "empresa_id": "empresa-teste",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        }

    return jwt.encode(claims, secret, algorithm="HS256")


def test_rota_protegida_sem_token():
    response = TestClient(app).get(ROTA)
    assert response.status_code == 401


def test_rota_protegida_com_token_invalido():
    response = TestClient(app).get(
        ROTA,
        headers={"Authorization": "Bearer token-invalido"},
    )
    assert response.status_code == 401


def test_rota_protegida_com_token_expirado():
    token = gerar_token({
        "sub": "usuario-teste",
        "empresa_id": "empresa-teste",
        "exp": datetime.now(timezone.utc) - timedelta(minutes=5),
    })

    response = TestClient(app).get(
        ROTA,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401


def test_rota_protegida_sem_empresa_id():
    token = gerar_token({
        "sub": "usuario-teste",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
    })

    response = TestClient(app).get(
        ROTA,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401


def test_rota_protegida_com_token_valido():
    token = gerar_token()

    response = TestClient(app).get(
        ROTA,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404

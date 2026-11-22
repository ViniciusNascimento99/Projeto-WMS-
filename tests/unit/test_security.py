
import jwt

from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient

from main import app

TEST_SECRET = "chave-de-teste-siglog-wms-32-bytes-minimo"
ROTA_PROTEGIDA = "/api/v1/products/test-id"


def gerar_token(secret=TEST_SECRET, expiracao=5):
    return jwt.encode(
        {
            "sub": "test-user",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=expiracao),
        },
        secret,
        algorithm="HS256",
    )


def test_rota_publica_health():
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200


def test_rota_protegida_sem_token(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", TEST_SECRET)
    client = TestClient(app)

    response = client.get(ROTA_PROTEGIDA)

    assert response.status_code == 401


def test_rota_protegida_com_token_valido(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", TEST_SECRET)
    client = TestClient(app)

    token = gerar_token()
    response = client.get(
        ROTA_PROTEGIDA,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code != 401


def test_rota_protegida_com_token_invalido(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", TEST_SECRET)
    client = TestClient(app)

    response = client.get(
        ROTA_PROTEGIDA,
        headers={"Authorization": "Bearer token-invalido"},
    )

    assert response.status_code == 401


def test_rota_protegida_com_token_expirado(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", TEST_SECRET)
    client = TestClient(app)

    token = jwt.encode(
        {
            "sub": "test-user",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=5),
        },
        TEST_SECRET,
        algorithm="HS256",
    )

    response = client.get(
        ROTA_PROTEGIDA,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401

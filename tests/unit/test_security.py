import jwt
import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient

from main import app
from src.config.request_context import RequestContext, get_request_context


SECRET = "chave-de-teste-siglog-wms-32-bytes-minimo"
ROTA = "/api/v1/products/produto-inexistente"


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


def test_rota_publica_health():
    response = TestClient(app).get("/health")
    assert response.status_code == 200


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

    app.dependency_overrides[get_request_context] = lambda: RequestContext(
        usuario_id="66666666-6666-4666-8666-666666666666",
        empresa_id="11111111-1111-4111-8111-111111111111",
        perfil_id="33333333-3333-4333-8333-333333333333",
    )

    try:
        response = TestClient(app).get(
            ROTA,
            headers={"Authorization": f"Bearer {token}"},
        )
    finally:
        app.dependency_overrides.pop(get_request_context, None)

    assert response.status_code == 404

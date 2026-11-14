"""Testes de contrato dos eventos (substitui o testar_eventos.py da raiz)."""
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from tests.conftest import API, estoque_pronto

RAIZ = Path(__file__).resolve().parents[2]
schema = json.loads((RAIZ / "events.schema.json").read_text(encoding="utf-8"))
exemplos = json.loads((RAIZ / "events.examples.json").read_text(encoding="utf-8"))
validador = Draft202012Validator(schema, format_checker=FormatChecker())


@pytest.mark.parametrize("nome", list(exemplos))
def test_exemplo_e_valido(nome):
    assert not list(validador.iter_errors(exemplos[nome])), nome


def test_evento_sem_shipment_id_e_rejeitado():
    quebrado = dict(exemplos["CargaExpedida"])
    del quebrado["shipmentId"]
    assert list(validador.iter_errors(quebrado))


def test_eventos_publicados_pela_api_seguem_o_schema(client, eventos):
    """Roda o fluxo inteiro e valida cada evento que o WMS publicou."""
    estoque_pronto(client, quantidade=10)
    client.post(f"{API}/picking", json={"orderId": "PED-1", "items": [{"productId": "SKU-1", "quantity": 10}]})
    pid = next(e["pickingId"] for e in eventos if e["event"] == "PickingCriado")
    client.post(f"{API}/picking/{pid}/pick", json={"productId": "SKU-1", "quantity": 10})
    client.post(f"{API}/packing", json={"orderId": "PED-1", "volumes": 2})
    client.post(f"{API}/shipments", json={"orderIds": ["PED-1"], "destination": "Recife - PE"})

    assert {e["event"] for e in eventos} == set(exemplos)  # os 7 eventos apareceram
    for evento in eventos:
        erros = [e.message for e in validador.iter_errors(evento)]
        assert not erros, (evento["event"], erros)

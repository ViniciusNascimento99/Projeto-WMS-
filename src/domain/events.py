"""Fábrica dos eventos de domínio.

Os eventos seguem o contrato events.schema.json (versão 1). Esta função só
monta o dicionário; quem publica (memória hoje, RabbitMQ depois) fica na
camada de infraestrutura.
"""
from datetime import datetime, timezone
from uuid import uuid4


def make_event(name: str, correlation_id: str, **fields) -> dict:
    return {
        "event": name,
        "version": 1,
        "eventId": str(uuid4()),
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "correlationId": correlation_id,
        "source": "wms",
        **fields,
    }

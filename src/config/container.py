"""Monta os objetos da aplicação (injeção de dependência simples)."""
import os

from src.application.services import WmsService
from src.infrastructure.events import InMemoryEventPublisher
from src.infrastructure.memory import InMemoryStore
from src.infrastructure.postgres.products import PostgresProductRepository

store = InMemoryStore()
publisher = InMemoryEventPublisher()

storage = os.environ.get("WMS_STORAGE", "memory").strip().lower()

product_repository = None

if storage == "postgres":
    product_repository = PostgresProductRepository()
elif storage != "memory":
    raise ValueError(f"Armazenamento não suportado: {storage}")

service = WmsService(store, publisher, product_repository)


def get_service() -> WmsService:
    return service


def reset() -> None:
    """Zera o estado. Usado pelos testes."""
    store.reset()
    publisher.reset()

"""Monta os objetos da aplicação (injeção de dependência simples)."""
from src.application.services import WmsService
from src.infrastructure.events import InMemoryEventPublisher
from src.infrastructure.memory import InMemoryStore

store = InMemoryStore()
publisher = InMemoryEventPublisher()
service = WmsService(store, publisher)


def get_service() -> WmsService:
    return service


def reset() -> None:
    """Zera o estado. Usado pelos testes."""
    store.reset()
    publisher.reset()

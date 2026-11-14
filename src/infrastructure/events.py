"""Publicação de eventos.

Hoje os eventos ficam numa lista em memória (útil para testes). A classe
do RabbitMQ terá o mesmo método publish() e publicará em siglog.wms.events.
"""


class InMemoryEventPublisher:
    def __init__(self):
        self.events: list[dict] = []

    def publish(self, event: dict) -> None:
        self.events.append(event)

    def reset(self) -> None:
        self.events.clear()

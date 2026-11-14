"""Persistência em memória.

É o ponto que o PostgreSQL vai substituir no Marco 2: a camada de aplicação
só fala com este objeto, então as regras do domínio não mudam.
"""
from src.domain.models import Inventory


class InMemoryStore:
    def __init__(self):
        self.reset()

    def reset(self) -> None:
        self.products = {}
        self.addresses = {}
        self.receipts = {}
        self.pickings = {}
        self.packings = {}
        self.shipments = {}
        self.inventory = Inventory()

    def has_sku(self, sku: str) -> bool:
        return any(p.sku == sku for p in self.products.values())

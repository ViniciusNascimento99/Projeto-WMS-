"""Modelo de domínio do WMS: entidades e regras de negócio.

Esta camada não conhece FastAPI, banco de dados nem RabbitMQ.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from src.domain.errors import DomainError


# ---------------------------------------------------------------- Cadastros
@dataclass
class Product:
    id: str
    sku: str
    description: str
    unit: str


@dataclass
class Address:
    code: str
    capacity: int
    aisle: str | None = None
    shelf: str | None = None
    level: int | None = None
    active: bool = True


# -------------------------------------------------------------- Recebimento
@dataclass
class ReceiptItem:
    product_id: str
    expected_quantity: int
    counted_quantity: int | None = None


@dataclass
class Receipt:
    id: str
    cargo_id: str
    invoice_number: str | None
    items: list[ReceiptItem]
    status: str = "AGUARDANDO"

    def conference(self, counted: dict[str, int]) -> bool:
        """UC02. Registra a contagem e devolve True se houver divergência."""
        if self.status != "AGUARDANDO":
            raise DomainError(
                "INVALID_RECEIPT_STATE",
                f"Receipt cannot be conferenced in status {self.status}",
            )
        if set(counted) != {i.product_id for i in self.items}:
            raise DomainError(
                "CONFERENCE_ITEMS_MISMATCH",
                "Conference products do not match receipt products",
            )
        has_divergence = False
        for item in self.items:
            item.counted_quantity = counted[item.product_id]
            if item.counted_quantity != item.expected_quantity:
                has_divergence = True
        self.status = "COM_DIVERGENCIA" if has_divergence else "CONFERIDA"
        return has_divergence


# ------------------------------------------------------------------ Estoque
@dataclass
class Movement:
    product_id: str
    type: str  # ENTRADA | SAIDA | AJUSTE
    quantity: int
    address_code: str
    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class Inventory:
    """Saldo por (produto, endereço), reservas e histórico de movimentações.

    Regras principais:
    - só se armazena o que foi recebido e conferido (awaiting_storage);
    - a soma dos saldos de um endereço nunca passa da capacidade;
    - o picking RESERVA a quantidade; a separação confirmada BAIXA o saldo;
    - o saldo nunca fica negativo e toda mudança gera uma movimentação.
    """

    def __init__(self):
        self._balance: dict[tuple[str, str], int] = {}
        self._reserved: dict[tuple[str, str], int] = {}
        self._awaiting: dict[str, int] = {}
        self.movements: list[Movement] = []

    # -- entrada ---------------------------------------------------------
    def receive(self, product_id: str, quantity: int) -> None:
        """Mercadoria conferida, aguardando um endereço."""
        self._awaiting[product_id] = self._awaiting.get(product_id, 0) + quantity

    def awaiting_storage(self, product_id: str) -> int:
        return self._awaiting.get(product_id, 0)

    def occupied(self, address_code: str) -> int:
        return sum(q for (_, a), q in self._balance.items() if a == address_code)

    def store(self, product_id: str, address: Address, quantity: int) -> int:
        """UC04. Guarda o produto no endereço e devolve o novo saldo."""
        if not address.active:
            raise DomainError("ADDRESS_INACTIVE", f"Address {address.code} is inactive")
        waiting = self.awaiting_storage(product_id)
        if quantity > waiting:
            raise DomainError(
                "NOT_RECEIVED",
                f"Only {waiting} unit(s) of {product_id} received and conferred "
                f"are awaiting storage",
            )
        free = address.capacity - self.occupied(address.code)
        if quantity > free:
            raise DomainError(
                "ADDRESS_CAPACITY_EXCEEDED",
                f"Address {address.code} has room for {free} unit(s)",
            )
        self._awaiting[product_id] = waiting - quantity
        key = (product_id, address.code)
        self._balance[key] = self._balance.get(key, 0) + quantity
        self.movements.append(Movement(product_id, "ENTRADA", quantity, address.code))
        return self._balance[key]

    # -- consulta --------------------------------------------------------
    def available(self, product_id: str) -> int:
        """Saldo físico menos o que já está reservado por outros pickings."""
        return sum(
            q - self._reserved.get(key, 0)
            for key, q in self._balance.items()
            if key[0] == product_id
        )

    def lines(self) -> list[dict]:
        return [
            {"productId": p, "addressCode": a, "quantity": q}
            for (p, a), q in sorted(self._balance.items())
            if q > 0
        ]

    def movements_of(self, product_id: str) -> list[Movement]:
        return sorted(
            (m for m in self.movements if m.product_id == product_id),
            key=lambda m: m.timestamp,
        )

    # -- saída -----------------------------------------------------------
    def reserve(self, requests: dict[str, int]) -> dict[str, list[tuple[str, int]]]:
        """UC06. Reserva tudo ou nada. Devolve, por produto, (endereço, qtd)."""
        for product_id, quantity in requests.items():
            if self.available(product_id) < quantity:
                raise DomainError(
                    "INSUFFICIENT_STOCK",
                    f"Insufficient stock for product {product_id}",
                )
        plan: dict[str, list[tuple[str, int]]] = {}
        for product_id, quantity in requests.items():
            remaining, lines = quantity, []
            for key in sorted(k for k in self._balance if k[0] == product_id):
                free = self._balance[key] - self._reserved.get(key, 0)
                take = min(free, remaining)
                if take > 0:
                    self._reserved[key] = self._reserved.get(key, 0) + take
                    lines.append((key[1], take))
                    remaining -= take
                if remaining == 0:
                    break
            plan[product_id] = lines
        return plan

    def pick(self, product_id: str, address_code: str, quantity: int) -> int:
        """UC07. Baixa o saldo reservado e devolve o novo saldo do endereço."""
        key = (product_id, address_code)
        self._reserved[key] -= quantity
        self._balance[key] -= quantity
        self.movements.append(Movement(product_id, "SAIDA", quantity, address_code))
        return self._balance[key]


# ------------------------------------------------------------------ Picking
@dataclass
class PickingItem:
    product_id: str
    address_code: str
    quantity: int
    picked: bool = False


@dataclass
class PickingOrder:
    id: str
    order_id: str
    items: list[PickingItem]
    status: str = "CRIADA"

    def confirm(self, product_id: str, quantity: int) -> list[PickingItem]:
        """UC07. Confirma a separação de um produto (todas as linhas dele)."""
        lines = [i for i in self.items if i.product_id == product_id]
        if not lines:
            raise DomainError(
                "PRODUCT_NOT_IN_PICKING",
                f"Product {product_id} is not in this picking order",
                status=404,
            )
        if all(i.picked for i in lines):
            raise DomainError("ALREADY_PICKED", "Product already picked")
        total = sum(i.quantity for i in lines)
        if quantity != total:
            raise DomainError(
                "QUANTITY_MISMATCH",
                f"Confirmed quantity must be {total}",
            )
        for line in lines:
            line.picked = True
        self.status = "SEPARADA" if all(i.picked for i in self.items) else "EM_SEPARACAO"
        return lines


# ------------------------------------------------------ Packing e expedição
@dataclass
class PackingOrder:
    id: str
    order_id: str
    volumes: int
    status: str = "EMBALADA"
    shipped: bool = False


@dataclass
class Shipment:
    shipment_id: str
    order_ids: list[str]
    destination: str
    shipped_at: str
    status: str = "EXPEDIDA"

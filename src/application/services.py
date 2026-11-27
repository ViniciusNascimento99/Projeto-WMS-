"""Casos de uso do WMS (UC01 a UC10).

Orquestra o domínio, grava no repositório e publica os eventos.
Devolve dicionários no formato do contrato (openapi.yaml).
"""
from dataclasses import asdict
from datetime import datetime, timezone
from uuid import uuid4

from src.domain.errors import DomainError, not_found
from src.domain.events import make_event
from src.domain.models import (
    Address,
    PackingOrder,
    PickingItem,
    PickingOrder,
    Product,
    Receipt,
    ReceiptItem,
    Shipment,
)


def _receipt_dto(r: Receipt) -> dict:
    return {
        "id": r.id,
        "cargoId": r.cargo_id,
        "status": r.status,
        "items": [
            {
                "productId": i.product_id,
                "expectedQuantity": i.expected_quantity,
                "countedQuantity": i.counted_quantity,
            }
            for i in r.items
        ],
    }


def _picking_dto(p: PickingOrder) -> dict:
    return {
        "id": p.id,
        "orderId": p.order_id,
        "status": p.status,
        "items": [
            {
                "productId": i.product_id,
                "addressCode": i.address_code,
                "quantity": i.quantity,
                "picked": i.picked,
            }
            for i in p.items
        ],
    }


def _packing_dto(p: PackingOrder) -> dict:
    return {"id": p.id, "orderId": p.order_id, "volumes": p.volumes, "status": p.status}


def _shipment_dto(s: Shipment) -> dict:
    return {
        "shipmentId": s.shipment_id,
        "orderIds": s.order_ids,
        "destination": s.destination,
        "status": s.status,
        "shippedAt": s.shipped_at,
    }


class WmsService:
    def __init__(self, store, publisher, product_repository=None):
        self.store = store
        self.publisher = publisher
        self.product_repository = product_repository

    def _emit(self, name: str, correlation_id: str, **fields) -> None:
        self.publisher.publish(make_event(name, correlation_id, **fields))
    # ----------------------------------------------------------- Produtos
    def create_product(
        self, sku: str, description: str, unit: str, empresa_id: str
    ) -> dict:
        if self.product_repository is not None:
            return self.product_repository.create(
                sku, description, unit, empresa_id
            )

        if self.store.has_sku(sku):
            raise DomainError("SKU_ALREADY_EXISTS", f"Product SKU {sku} already exists")
        product = Product(id=str(uuid4()), sku=sku, description=description, unit=unit)
        self.store.products[product.id] = product
        return asdict(product)

    def get_product(self, product_id: str, empresa_id: str) -> dict:
        if self.product_repository is not None:
            product = self.product_repository.get_by_id(product_id, empresa_id)
            if product is None:
                raise not_found("PRODUCT_NOT_FOUND", "Product not found")
            return product

        product = self.store.products.get(product_id)
        if product is None:
            raise not_found("PRODUCT_NOT_FOUND", "Product not found")
        return asdict(product)

    # ---------------------------------------------------------- Endereços
    def create_address(self, code, capacity, aisle, shelf, level) -> dict:
        if code in self.store.addresses:
            raise DomainError("ADDRESS_ALREADY_EXISTS", f"Address {code} already exists")
        address = Address(code, capacity, aisle, shelf, level)
        self.store.addresses[code] = address
        return asdict(address)

    # -------------------------------------------------------- Recebimento
    def create_receipt(self, cargo_id, invoice_number, items: list[tuple[str, int]]) -> dict:
        product_ids = [pid for pid, _ in items]
        if len(set(product_ids)) != len(product_ids):
            raise DomainError("DUPLICATE_ITEMS", "Repeated product in receipt", status=422)
        for pid in product_ids:
            if not self.store.has_sku(pid):
                raise not_found("PRODUCT_NOT_FOUND", f"Product {pid} not found")
        receipt = Receipt(
            id=str(uuid4()),
            cargo_id=cargo_id,
            invoice_number=invoice_number,
            items=[ReceiptItem(pid, qty) for pid, qty in items],
        )
        self.store.receipts[receipt.id] = receipt
        return _receipt_dto(receipt)

    def conference_receipt(self, receipt_id: str, counted: list[tuple[str, int]]) -> dict:
        receipt = self.store.receipts.get(receipt_id)
        if receipt is None:
            raise not_found("RECEIPT_NOT_FOUND", "Receipt not found")
        counted_by_product = dict(counted)
        if len(counted_by_product) != len(counted):
            raise DomainError("DUPLICATE_ITEMS", "Repeated product in conference", status=422)

        has_divergence = receipt.conference(counted_by_product)

        if not has_divergence:
            for item in receipt.items:
                self.store.inventory.receive(item.product_id, item.counted_quantity)
            fields = {
                "cargoId": receipt.cargo_id,
                "receiptId": receipt.id,
                "items": [
                    {"productId": i.product_id, "quantity": i.counted_quantity}
                    for i in receipt.items
                ],
            }
            if receipt.invoice_number:
                fields["invoiceNumber"] = receipt.invoice_number
            self._emit("MercadoriaRecebida", receipt.cargo_id, **fields)
        return _receipt_dto(receipt)

    # ------------------------------------------------------------- Estoque
    def allocate(self, product_id: str, address_code: str, quantity: int) -> dict:
        if not self.store.has_sku(product_id):
            raise not_found("PRODUCT_NOT_FOUND", "Product not found")
        address = self.store.addresses.get(address_code)
        if address is None:
            raise not_found("ADDRESS_NOT_FOUND", "Address not found")

        balance = self.store.inventory.store(product_id, address, quantity)

        self._emit(
            "ProdutoArmazenado", product_id,
            productId=product_id, addressCode=address_code, quantity=quantity,
        )
        self._emit(
            "EstoqueAtualizado", product_id,
            productId=product_id, addressCode=address_code,
            delta=quantity, balance=balance, reason="ARMAZENAGEM",
        )
        return {"productId": product_id, "addressCode": address_code, "quantity": balance}

    def get_inventory(self, address: str | None, page: int, size: int) -> list[dict]:
        lines = self.store.inventory.lines()
        if address:
            lines = [l for l in lines if l["addressCode"] == address]
        start = (page - 1) * size
        return lines[start:start + size]

    def get_product_inventory(self, product_id: str) -> list[dict]:
        if not self.store.has_sku(product_id):
            raise not_found("PRODUCT_NOT_FOUND", "Product not found")
        return [l for l in self.store.inventory.lines() if l["productId"] == product_id]

    def get_product_movements(self, product_id: str) -> list[dict]:
        if not self.store.has_sku(product_id):
            raise not_found("PRODUCT_NOT_FOUND", "Product not found")
        return [
            {
                "id": m.id,
                "productId": m.product_id,
                "type": m.type,
                "quantity": m.quantity,
                "addressCode": m.address_code,
                "timestamp": m.timestamp,
            }
            for m in self.store.inventory.movements_of(product_id)
        ]

    # ------------------------------------------------------------- Picking
    def create_picking(self, order_id: str, items: list[tuple[str, int]]) -> dict:
        if any(p.order_id == order_id and p.status != "CANCELADA"
               for p in self.store.pickings.values()):
            raise DomainError("PICKING_ALREADY_EXISTS", f"Order {order_id} already has a picking order")

        requests: dict[str, int] = {}
        for pid, qty in items:  # soma linhas repetidas do mesmo produto
            requests[pid] = requests.get(pid, 0) + qty

        plan = self.store.inventory.reserve(requests)  # tudo ou nada

        picking = PickingOrder(
            id=str(uuid4()),
            order_id=order_id,
            items=[
                PickingItem(pid, address, qty)
                for pid, lines in plan.items()
                for address, qty in lines
            ],
        )
        self.store.pickings[picking.id] = picking
        self._emit("PickingCriado", order_id, pickingId=picking.id, orderId=order_id)
        return _picking_dto(picking)

    def confirm_pick(self, picking_id: str, product_id: str, quantity: int) -> dict:
        picking = self.store.pickings.get(picking_id)
        if picking is None:
            raise not_found("PICKING_NOT_FOUND", "Picking order not found")

        for line in picking.confirm(product_id, quantity):
            balance = self.store.inventory.pick(line.product_id, line.address_code, line.quantity)
            self._emit(
                "EstoqueAtualizado", picking.order_id,
                productId=line.product_id, addressCode=line.address_code,
                delta=-line.quantity, balance=balance, reason="SEPARACAO",
            )
        if picking.status == "SEPARADA":
            self._emit("PedidoSeparado", picking.order_id,
                       pickingId=picking.id, orderId=picking.order_id)
        return _picking_dto(picking)

    # -------------------------------------------------------------- Packing
    def create_packing(self, order_id: str, volumes: int) -> dict:
        picking = next(
            (p for p in self.store.pickings.values()
             if p.order_id == order_id and p.status != "CANCELADA"),
            None,
        )
        if picking is None or picking.status != "SEPARADA":
            raise DomainError("ORDER_NOT_PICKED", f"Order {order_id} is not fully picked")
        if order_id in self.store.packings:
            raise DomainError("ORDER_ALREADY_PACKED", f"Order {order_id} is already packed")

        packing = PackingOrder(id=str(uuid4()), order_id=order_id, volumes=volumes)
        self.store.packings[order_id] = packing
        self._emit("PedidoEmbalado", order_id,
                   packingId=packing.id, orderId=order_id, volumes=volumes)
        return _packing_dto(packing)

    # ------------------------------------------------------------ Expedição
    def create_shipment(self, order_ids: list[str], destination: str) -> dict:
        if len(set(order_ids)) != len(order_ids):
            raise DomainError("DUPLICATE_ORDERS", "Repeated order in shipment", status=422)
        for order_id in order_ids:
            packing = self.store.packings.get(order_id)
            if packing is None or packing.status != "EMBALADA":
                raise DomainError("ORDER_NOT_PACKED", f"Order {order_id} is not packed")
            if packing.shipped:
                raise DomainError("ORDER_ALREADY_SHIPPED", f"Order {order_id} already shipped")

        shipment = Shipment(
            shipment_id=str(uuid4()),
            order_ids=order_ids,
            destination=destination,
            shipped_at=datetime.now(timezone.utc).isoformat(),
        )
        for order_id in order_ids:
            self.store.packings[order_id].shipped = True
        self.store.shipments[shipment.shipment_id] = shipment
        self._emit("CargaExpedida", order_ids[0],
                   shipmentId=shipment.shipment_id, orderIds=order_ids, destination=destination)
        return _shipment_dto(shipment)

    def get_shipment(self, shipment_id: str) -> dict:
        shipment = self.store.shipments.get(shipment_id)
        if shipment is None:
            raise not_found("SHIPMENT_NOT_FOUND", "Shipment not found")
        return _shipment_dto(shipment)

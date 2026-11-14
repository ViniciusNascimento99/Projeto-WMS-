"""Modelos de entrada e saída da API (seguem o openapi.yaml)."""
from pydantic import BaseModel, Field

NonEmpty = Field(min_length=1)


# ----- entrada
class ProductCreate(BaseModel):
    sku: str = NonEmpty
    description: str = NonEmpty
    unit: str = NonEmpty


class AddressCreate(BaseModel):
    code: str = NonEmpty
    capacity: int = Field(ge=1)
    aisle: str | None = None
    shelf: str | None = None
    level: int | None = None


class ReceiptItemIn(BaseModel):
    productId: str = NonEmpty
    expectedQuantity: int = Field(ge=1)


class ReceiptCreate(BaseModel):
    cargoId: str = NonEmpty
    invoiceNumber: str | None = None
    items: list[ReceiptItemIn] = Field(min_length=1)


class ConferenceItem(BaseModel):
    productId: str = NonEmpty
    countedQuantity: int = Field(ge=0)


class ConferenceRequest(BaseModel):
    items: list[ConferenceItem] = Field(min_length=1)


class AllocationCreate(BaseModel):
    productId: str = NonEmpty
    addressCode: str = NonEmpty
    quantity: int = Field(ge=1)


class PickingItemIn(BaseModel):
    productId: str = NonEmpty
    quantity: int = Field(ge=1)


class PickingCreate(BaseModel):
    orderId: str = NonEmpty
    items: list[PickingItemIn] = Field(min_length=1)


class PickConfirm(BaseModel):
    productId: str = NonEmpty
    quantity: int = Field(ge=1)


class PackingCreate(BaseModel):
    orderId: str = NonEmpty
    volumes: int = Field(default=1, ge=1)


class ShipmentCreate(BaseModel):
    orderIds: list[str] = Field(min_length=1)
    destination: str = NonEmpty


# ----- saída
class Product(BaseModel):
    id: str
    sku: str
    description: str
    unit: str


class Address(BaseModel):
    code: str
    capacity: int
    aisle: str | None = None
    shelf: str | None = None
    level: int | None = None
    active: bool


class ReceiptItemOut(BaseModel):
    productId: str
    expectedQuantity: int
    countedQuantity: int | None = None


class Receipt(BaseModel):
    id: str
    cargoId: str
    status: str
    items: list[ReceiptItemOut]


class InventoryItem(BaseModel):
    productId: str
    addressCode: str
    quantity: int


class Movement(BaseModel):
    id: str
    productId: str
    type: str
    quantity: int
    addressCode: str
    timestamp: str


class PickingItemOut(BaseModel):
    productId: str
    addressCode: str
    quantity: int
    picked: bool


class PickingOrder(BaseModel):
    id: str
    orderId: str
    status: str
    items: list[PickingItemOut]


class PackingOrder(BaseModel):
    id: str
    orderId: str
    volumes: int
    status: str


class Shipment(BaseModel):
    shipmentId: str
    orderIds: list[str]
    destination: str
    status: str
    shippedAt: str | None = None

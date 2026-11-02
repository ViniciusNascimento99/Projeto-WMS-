
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


router = APIRouter(prefix="/receipts", tags=["Receipts"])


class ReceiptItem(BaseModel):
    productId: str
    expectedQuantity: int
    countedQuantity: int | None = None


class ReceiptCreate(BaseModel):
    cargoId: str
    invoiceNumber: str | None = None
    items: list[ReceiptItem]


class ConferenceItem(BaseModel):
    productId: str
    countedQuantity: int


class ConferenceRequest(BaseModel):
    items: list[ConferenceItem]


class Receipt(BaseModel):
    id: str
    cargoId: str
    status: str
    items: list[ReceiptItem]


receipts = {}


@router.post("", status_code=201, response_model=Receipt)
def create_receipt(receipt: ReceiptCreate):
    receipt_id = str(uuid4())

    new_receipt = Receipt(
        id=receipt_id,
        cargoId=receipt.cargoId,
        status="AGUARDANDO",
        items=receipt.items,
    )

    receipts[receipt_id] = new_receipt

    return new_receipt


@router.post("/{id}/conference", response_model=Receipt)
def conference_receipt(id: str, conference: ConferenceRequest):
    receipt = receipts.get(id)

    if receipt is None:
        raise HTTPException(
            status_code=404,
            detail="Receipt not found",
        )

    if receipt.status != "AGUARDANDO":
        raise HTTPException(
            status_code=409,
            detail="Receipt cannot be conferenced in its current status",
        )

    expected_products = {
        item.productId: item
        for item in receipt.items
    }

    counted_products = {
        item.productId: item.countedQuantity
        for item in conference.items
    }

    if set(expected_products) != set(counted_products):
        raise HTTPException(
            status_code=409,
            detail="Conference products do not match receipt products",
        )

    has_divergence = False

    for product_id, item in expected_products.items():
        counted_quantity = counted_products[product_id]

        item.countedQuantity = counted_quantity

        if item.expectedQuantity != counted_quantity:
            has_divergence = True

    if has_divergence:
        receipt.status = "COM_DIVERGENCIA"
    else:
        receipt.status = "CONFERIDA"

    return receipt

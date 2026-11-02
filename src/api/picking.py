
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from uuid import uuid4

from src.api.allocations import allocations


router = APIRouter(prefix="/picking", tags=["Picking"])


class PickingItemCreate(BaseModel):
    productId: str
    quantity: int = Field(ge=1)


class PickingCreate(BaseModel):
    orderId: str
    items: list[PickingItemCreate]


class PickConfirm(BaseModel):
    productId: str
    quantity: int = Field(ge=1)


picking_orders = {}


# Criar ordem de separação
@router.post("", status_code=201)
def create_picking(picking: PickingCreate):

    picking_items = []

    for item in picking.items:

        product_allocations = [
            allocation for allocation in allocations
            if allocation["productId"] == item.productId
        ]

        if not product_allocations:
            raise HTTPException(
                status_code=404,
                detail=f"Product {item.productId} not found in inventory"
            )

        available_quantity = sum(
            allocation["quantity"]
            for allocation in product_allocations
        )

        if available_quantity < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for product {item.productId}"
            )

        picking_items.append({
            "productId": item.productId,
            "addressCode": product_allocations[0]["addressCode"],
            "quantity": item.quantity,
            "picked": False
        })

    new_picking = {
        "id": str(uuid4()),
        "orderId": picking.orderId,
        "status": "CRIADA",
        "items": picking_items
    }

    picking_orders[new_picking["id"]] = new_picking

    return new_picking


# Confirmar separação de produto
@router.post("/{id}/pick")
def confirm_pick(id: str, confirmation: PickConfirm):

    if id not in picking_orders:
        raise HTTPException(
            status_code=404,
            detail="Picking order not found"
        )

    picking = picking_orders[id]

    item_found = False

    for item in picking["items"]:

        if item["productId"] == confirmation.productId:

            if confirmation.quantity != item["quantity"]:
                raise HTTPException(
                    status_code=400,
                    detail="Confirmed quantity must match picking quantity"
                )

            if item["picked"]:
                raise HTTPException(
                    status_code=400,
                    detail="Product already picked"
                )

            item["picked"] = True
            item_found = True
            break

    if not item_found:
        raise HTTPException(
            status_code=404,
            detail="Product not found in picking order"
        )

    if all(item["picked"] for item in picking["items"]):
        picking["status"] = "SEPARADA"
    else:
        picking["status"] = "EM_SEPARACAO"

    return picking


from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from uuid import uuid4
from datetime import datetime, timezone

from src.api.products import products
from src.api.addresses import addresses


router = APIRouter(prefix="/allocations", tags=["Allocations"])


class AllocationCreate(BaseModel):
    productId: str
    addressCode: str
    quantity: int = Field(ge=1)


allocations = []
movements = []


@router.post("", status_code=201)
def create_allocation(allocation: AllocationCreate):

    product_exists = any(
        product["sku"] == allocation.productId
        for product in products.values()
    )

    if not product_exists:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    if allocation.addressCode not in addresses:
        raise HTTPException(
            status_code=404,
            detail="Address not found"
        )

    new_allocation = {
        "productId": allocation.productId,
        "addressCode": allocation.addressCode,
        "quantity": allocation.quantity
    }

    allocations.append(new_allocation)

    # Registra a movimentação de entrada
    new_movement = {
        "id": str(uuid4()),
        "productId": allocation.productId,
        "type": "ENTRADA",
        "quantity": allocation.quantity,
        "addressCode": allocation.addressCode,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    movements.append(new_movement)

    return new_allocation

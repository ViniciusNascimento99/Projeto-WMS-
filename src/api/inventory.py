
from fastapi import APIRouter, Query, HTTPException

from src.api.allocations import allocations, movements


router = APIRouter(prefix="/inventory", tags=["Inventory"])


# Consultar estoque geral
@router.get("")
def get_inventory(
    address: str | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1)
):
    inventory = allocations.copy()

    if address:
        inventory = [
            item for item in inventory
            if item["addressCode"] == address
        ]

    start = (page - 1) * size
    end = start + size

    return inventory[start:end]


# Consultar saldo de um produto por endereço
@router.get("/{product_id}")
def get_product_inventory(product_id: str):

    product_inventory = [
        item for item in allocations
        if item["productId"] == product_id
    ]

    if not product_inventory:
        raise HTTPException(
            status_code=404,
            detail="Product inventory not found"
        )

    return product_inventory


# Consultar histórico de movimentações
@router.get("/{product_id}/movements")
def get_product_movements(product_id: str):

    product_movements = [
        movement for movement in movements
        if movement["productId"] == product_id
    ]

    if not product_movements:
        raise HTTPException(
            status_code=404,
            detail="Product movements not found"
        )

    return sorted(
        product_movements,
        key=lambda movement: movement["timestamp"]
    )

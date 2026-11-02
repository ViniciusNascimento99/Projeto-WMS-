from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from uuid import uuid4

from src.api.picking import picking_orders


router = APIRouter(prefix="/packing", tags=["Packing"])


class PackingCreate(BaseModel):
    orderId: str
    volumes: int = Field(default=1, ge=1)


packing_orders = {}


# Criar ordem de embalagem
@router.post("", status_code=201)
def create_packing(packing: PackingCreate):

    picking = next(
        (
            order for order in picking_orders.values()
            if order["orderId"] == packing.orderId
        ),
        None
    )

    if not picking:
        raise HTTPException(
            status_code=404,
            detail="Picking order not found"
        )

    if picking["status"] != "SEPARADA":
        raise HTTPException(
            status_code=400,
            detail="Picking order is not completed"
        )

    new_packing = {
        "id": str(uuid4()),
        "orderId": packing.orderId,
        "volumes": packing.volumes,
        "status": "EMBALADA"
    }

    packing_orders[new_packing["id"]] = new_packing

    return new_packing
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import uuid4


router = APIRouter(prefix="/shipments", tags=["Shipments"])


class ShipmentCreate(BaseModel):
    orderIds: list[str]
    destination: str


shipments = {}


# Criar expedição
@router.post("", status_code=201)
def create_shipment(shipment: ShipmentCreate):

    new_shipment = {
        "shipmentId": str(uuid4()),
        "orderIds": shipment.orderIds,
        "destination": shipment.destination,
        "status": "PLANEJADA",
        "shippedAt": None
    }

    shipments[new_shipment["shipmentId"]] = new_shipment

    return new_shipment


# Consultar expedição
@router.get("/{id}")
def get_shipment(id: str):

    if id not in shipments:
        raise HTTPException(
            status_code=404,
            detail="Shipment not found"
        )

    return shipments[id]
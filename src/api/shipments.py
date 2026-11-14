from fastapi import APIRouter, Depends

from src.api import schemas
from src.application.services import WmsService
from src.config.container import get_service

router = APIRouter(prefix="/shipments", tags=["Shipments"])


@router.post("", status_code=201, response_model=schemas.Shipment)
def create_shipment(body: schemas.ShipmentCreate, svc: WmsService = Depends(get_service)):
    return svc.create_shipment(body.orderIds, body.destination)


@router.get("/{id}", response_model=schemas.Shipment)
def get_shipment(id: str, svc: WmsService = Depends(get_service)):
    return svc.get_shipment(id)

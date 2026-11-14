from fastapi import APIRouter, Depends

from src.api import schemas
from src.application.services import WmsService
from src.config.container import get_service

router = APIRouter(prefix="/picking", tags=["Picking"])


@router.post("", status_code=201, response_model=schemas.PickingOrder)
def create_picking(body: schemas.PickingCreate, svc: WmsService = Depends(get_service)):
    items = [(i.productId, i.quantity) for i in body.items]
    return svc.create_picking(body.orderId, items)


@router.post("/{id}/pick", response_model=schemas.PickingOrder)
def confirm_pick(id: str, body: schemas.PickConfirm, svc: WmsService = Depends(get_service)):
    return svc.confirm_pick(id, body.productId, body.quantity)

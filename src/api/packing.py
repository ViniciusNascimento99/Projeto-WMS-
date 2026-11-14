from fastapi import APIRouter, Depends

from src.api import schemas
from src.application.services import WmsService
from src.config.container import get_service

router = APIRouter(prefix="/packing", tags=["Packing"])


@router.post("", status_code=201, response_model=schemas.PackingOrder)
def create_packing(body: schemas.PackingCreate, svc: WmsService = Depends(get_service)):
    return svc.create_packing(body.orderId, body.volumes)

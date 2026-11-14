from fastapi import APIRouter, Depends

from src.api import schemas
from src.application.services import WmsService
from src.config.container import get_service

router = APIRouter(prefix="/addresses", tags=["Addresses"])


@router.post("", status_code=201, response_model=schemas.Address, response_model_exclude_none=True)
def create_address(body: schemas.AddressCreate, svc: WmsService = Depends(get_service)):
    return svc.create_address(body.code, body.capacity, body.aisle, body.shelf, body.level)

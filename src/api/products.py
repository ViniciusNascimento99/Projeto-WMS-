from fastapi import APIRouter, Depends

from src.api import schemas
from src.application.services import WmsService
from src.config.container import get_service

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("", status_code=201, response_model=schemas.Product)
def create_product(body: schemas.ProductCreate, svc: WmsService = Depends(get_service)):
    return svc.create_product(body.sku, body.description, body.unit)


@router.get("/{id}", response_model=schemas.Product)
def get_product(id: str, svc: WmsService = Depends(get_service)):
    return svc.get_product(id)

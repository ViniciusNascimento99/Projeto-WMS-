from fastapi import APIRouter, Depends, Query

from src.api import schemas
from src.application.services import WmsService
from src.config.container import get_service

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("", response_model=list[schemas.InventoryItem])
def get_inventory(
    address: str | None = None,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1),
    svc: WmsService = Depends(get_service),
):
    return svc.get_inventory(address, page, size)


@router.get("/{product_id}", response_model=list[schemas.InventoryItem])
def get_product_inventory(product_id: str, svc: WmsService = Depends(get_service)):
    return svc.get_product_inventory(product_id)


@router.get("/{product_id}/movements", response_model=list[schemas.Movement])
def get_product_movements(product_id: str, svc: WmsService = Depends(get_service)):
    return svc.get_product_movements(product_id)

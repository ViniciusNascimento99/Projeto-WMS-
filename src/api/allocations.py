from fastapi import APIRouter, Depends

from src.api import schemas
from src.application.services import WmsService
from src.config.container import get_service

router = APIRouter(prefix="/allocations", tags=["Allocations"])


@router.post("", status_code=201, response_model=schemas.InventoryItem)
def create_allocation(body: schemas.AllocationCreate, svc: WmsService = Depends(get_service)):
    return svc.allocate(body.productId, body.addressCode, body.quantity)

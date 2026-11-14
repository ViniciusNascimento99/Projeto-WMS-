from fastapi import APIRouter, Depends

from src.api import schemas
from src.application.services import WmsService
from src.config.container import get_service

router = APIRouter(prefix="/receipts", tags=["Receipts"])


@router.post("", status_code=201, response_model=schemas.Receipt, response_model_exclude_none=True)
def create_receipt(body: schemas.ReceiptCreate, svc: WmsService = Depends(get_service)):
    items = [(i.productId, i.expectedQuantity) for i in body.items]
    return svc.create_receipt(body.cargoId, body.invoiceNumber, items)


@router.post("/{id}/conference", response_model=schemas.Receipt, response_model_exclude_none=True)
def conference_receipt(id: str, body: schemas.ConferenceRequest,
                       svc: WmsService = Depends(get_service)):
    counted = [(i.productId, i.countedQuantity) for i in body.items]
    return svc.conference_receipt(id, counted)

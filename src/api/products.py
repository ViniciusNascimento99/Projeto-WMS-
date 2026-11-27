from fastapi import APIRouter, Depends

from src.api import schemas
from src.application.services import WmsService
from src.config.container import get_service
from src.config.request_context import RequestContext, get_request_context

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("", status_code=201, response_model=schemas.Product)
def create_product(
    body: schemas.ProductCreate,
    context: RequestContext = Depends(get_request_context),
    svc: WmsService = Depends(get_service),
):
    return svc.create_product(
        body.sku,
        body.description,
        body.unit,
        context.empresa_id,
    )


@router.get("/{id}", response_model=schemas.Product)
def get_product(
    id: str,
    context: RequestContext = Depends(get_request_context),
    svc: WmsService = Depends(get_service),
):
    return svc.get_product(id, context.empresa_id)

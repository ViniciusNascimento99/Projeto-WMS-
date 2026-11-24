from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.api.addresses import router as addresses_router
from src.api.allocations import router as allocations_router
from src.api.inventory import router as inventory_router
from src.api.packing import router as packing_router
from src.api.picking import router as picking_router
from src.api.products import router as products_router
from src.api.receipts import router as receipts_router
from src.api.shipments import router as shipments_router
from src.domain.errors import DomainError
from src.config.security import require_auth

app = FastAPI(
    title="SIG-Log WMS",
    description="API de Gestão de Estoque e Centro de Distribuição",
    version="1.0.0",
)


# Erros no formato do contrato: {"code": "...", "message": "..."}
@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError):
    return JSONResponse(status_code=exc.status, content={"code": exc.code, "message": exc.message})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    first = exc.errors()[0]
    where = ".".join(str(part) for part in first["loc"] if part != "body")
    return JSONResponse(
        status_code=422,
        content={"code": "VALIDATION_ERROR", "message": f"{where}: {first['msg']}"},
    )


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request: Request, exc: StarletteHTTPException):
    # JSON malformado chega como 400; o contrato trata como erro de validação (422)
    if exc.status_code == 400:
        return JSONResponse(status_code=422, content={"code": "VALIDATION_ERROR", "message": "Invalid request body"})
    return JSONResponse(status_code=exc.status_code, content={"code": "HTTP_ERROR", "message": str(exc.detail)})


@app.get("/")
def inicio():
    return {"sistema": "SIG-Log WMS", "status": "online"}


@app.get("/health")
def verificar_saude():
    return {"status": "healthy"}


# Rotas da API versão 1
for router in (
    products_router, addresses_router, receipts_router, allocations_router,
    inventory_router, picking_router, packing_router, shipments_router,
):
    app.include_router(
        router,
        prefix="/api/v1",
        dependencies=[Depends(require_auth)],
    )

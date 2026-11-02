from fastapi import FastAPI

from src.api.products import router as products_router
from src.api.addresses import router as addresses_router
from src.api.receipts import router as receipts_router
from src.api.allocations import router as allocations_router
from src.api.inventory import router as inventory_router
from src.api.picking import router as picking_router
from src.api.packing import router as packing_router
from src.api.shipments import router as shipments_router


app = FastAPI(
    title="SIG-Log WMS",
    description="API de Gestão de Estoque e Centro de Distribuição",
    version="1.0.0"
)


@app.get("/")
def inicio():
    return {
        "sistema": "SIG-Log WMS",
        "status": "online"
    }


@app.get("/health")
def verificar_saude():
    return {
        "status": "healthy"
    }


# Rotas da API versão 1
app.include_router(products_router, prefix="/api/v1")
app.include_router(addresses_router, prefix="/api/v1")
app.include_router(receipts_router, prefix="/api/v1")
app.include_router(allocations_router, prefix="/api/v1")
app.include_router(inventory_router, prefix="/api/v1")
app.include_router(picking_router, prefix="/api/v1")
app.include_router(packing_router, prefix="/api/v1")
app.include_router(shipments_router, prefix="/api/v1")
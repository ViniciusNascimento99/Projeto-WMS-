
from fastapi import FastAPI
from src.api.products import router as products_router

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


app.include_router(products_router)

from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


router = APIRouter(prefix="/products", tags=["Products"])


class ProductCreate(BaseModel):
    sku: str
    description: str
    unit: str


class Product(ProductCreate):
    id: str


products = {}


@router.post("", status_code=201, response_model=Product)
def create_product(product: ProductCreate):
    for existing_product in products.values():
        if existing_product["sku"] == product.sku:
            raise HTTPException(
                status_code=409,
                detail="Product SKU already exists",
            )

    product_id = str(uuid4())

    new_product = {
        "id": product_id,
        "sku": product.sku,
        "description": product.description,
        "unit": product.unit,
    }

    products[product_id] = new_product

    return new_product


@router.get("/{id}", response_model=Product)
def get_product(id: str):
    product = products.get(id)

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    return product
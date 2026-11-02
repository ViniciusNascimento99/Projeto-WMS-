
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


router = APIRouter(prefix="/addresses", tags=["Addresses"])


class AddressCreate(BaseModel):
    code: str
    capacity: int
    aisle: str | None = None
    shelf: str | None = None
    level: int | None = None


class Address(AddressCreate):
    active: bool = True


addresses = {}


@router.post("", status_code=201, response_model=Address)
def create_address(address: AddressCreate):
    if address.code in addresses:
        raise HTTPException(
            status_code=409,
            detail="Address code already exists",
        )

    new_address = Address(
        code=address.code,
        capacity=address.capacity,
        aisle=address.aisle,
        shelf=address.shelf,
        level=address.level,
        active=True,
    )

    addresses[address.code] = new_address

    return new_address

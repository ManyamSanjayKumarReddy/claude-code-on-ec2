from decimal import Decimal

from pydantic import BaseModel, Field


class CartItemAdd(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1, le=100)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1, le=100)


class CartItemRead(BaseModel):
    product_id: int
    name: str
    price: Decimal
    image_url: str | None
    quantity: int
    stock_quantity: int
    line_total: Decimal


class CartRead(BaseModel):
    items: list[CartItemRead]
    total: Decimal
    item_count: int

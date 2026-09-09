from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

SHIPPING_METHODS: dict[str, Decimal] = {
    "standard": Decimal("5.00"),
    "express": Decimal("15.00"),
}

SHIPPING_METHOD_LABELS: dict[str, str] = {
    "standard": "Standard shipping (5-7 business days)",
    "express": "Express shipping (1-2 business days)",
}


class ShippingMethodRead(BaseModel):
    code: str
    label: str
    cost: Decimal


class CheckoutRequest(BaseModel):
    recipient_name: str = Field(min_length=1, max_length=200)
    address_line1: str = Field(min_length=1, max_length=255)
    address_line2: str | None = Field(default=None, max_length=255)
    city: str = Field(min_length=1, max_length=100)
    state: str = Field(min_length=1, max_length=100)
    postal_code: str = Field(min_length=1, max_length=20)
    country: str = Field(min_length=1, max_length=100)
    shipping_method: str


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_name: str
    unit_price: Decimal
    quantity: int


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    recipient_name: str
    address_line1: str
    address_line2: str | None
    city: str
    state: str
    postal_code: str
    country: str
    shipping_method: str
    shipping_cost: Decimal
    subtotal: Decimal
    total: Decimal
    created_at: datetime
    items: list[OrderItemRead]

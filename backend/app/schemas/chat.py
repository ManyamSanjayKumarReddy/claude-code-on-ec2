from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


class ChatProductRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: Decimal
    image_url: str | None
    stock_quantity: int


class ChatResponse(BaseModel):
    reply: str
    products: list[ChatProductRef] = []

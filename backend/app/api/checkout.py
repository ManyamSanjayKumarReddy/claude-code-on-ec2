from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from tortoise.transactions import in_transaction

from app.core.security import get_current_user
from app.models.cart_item import CartItem
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.user import User
from app.schemas.order import (
    SHIPPING_METHOD_LABELS,
    SHIPPING_METHODS,
    CheckoutRequest,
    OrderRead,
    ShippingMethodRead,
)

checkout_router = APIRouter(prefix="/checkout", tags=["checkout"])
orders_router = APIRouter(prefix="/orders", tags=["orders"])


@checkout_router.get("/shipping-methods", response_model=list[ShippingMethodRead])
async def list_shipping_methods() -> list[ShippingMethodRead]:
    return [
        ShippingMethodRead(code=code, label=SHIPPING_METHOD_LABELS[code], cost=cost)
        for code, cost in SHIPPING_METHODS.items()
    ]


@checkout_router.post("", response_model=OrderRead, status_code=201)
async def checkout(payload: CheckoutRequest, current_user: User = Depends(get_current_user)) -> Order:
    if payload.shipping_method not in SHIPPING_METHODS:
        raise HTTPException(status_code=400, detail="Unknown shipping method")

    cart_items = await CartItem.filter(user=current_user).prefetch_related("product")
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    for item in cart_items:
        if item.quantity > item.product.stock_quantity:
            raise HTTPException(status_code=400, detail=f"Not enough stock for {item.product.name}")

    subtotal = sum((item.product.price * item.quantity for item in cart_items), Decimal("0"))
    shipping_cost = SHIPPING_METHODS[payload.shipping_method]

    async with in_transaction():
        order = await Order.create(
            user=current_user,
            recipient_name=payload.recipient_name,
            address_line1=payload.address_line1,
            address_line2=payload.address_line2,
            city=payload.city,
            state=payload.state,
            postal_code=payload.postal_code,
            country=payload.country,
            shipping_method=payload.shipping_method,
            shipping_cost=shipping_cost,
            subtotal=subtotal,
            total=subtotal + shipping_cost,
        )
        for item in cart_items:
            await OrderItem.create(
                order=order,
                product=item.product,
                product_name=item.product.name,
                unit_price=item.product.price,
                quantity=item.quantity,
            )
            item.product.stock_quantity -= item.quantity
            await item.product.save()
        await CartItem.filter(user=current_user).delete()

    await order.refresh_from_db()
    await order.fetch_related("items")
    return order


@orders_router.get("", response_model=list[OrderRead])
async def list_orders(current_user: User = Depends(get_current_user)) -> list[Order]:
    return await Order.filter(user=current_user).prefetch_related("items")


@orders_router.get("/{order_id}", response_model=OrderRead)
async def get_order(order_id: int, current_user: User = Depends(get_current_user)) -> Order:
    order = await Order.get_or_none(id=order_id, user=current_user).prefetch_related("items")
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

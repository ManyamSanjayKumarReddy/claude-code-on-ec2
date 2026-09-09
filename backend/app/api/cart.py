from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException

from app.core.security import get_current_user
from app.models.cart_item import CartItem
from app.models.product import Product
from app.models.user import User
from app.schemas.cart import CartItemAdd, CartItemRead, CartItemUpdate, CartRead

router = APIRouter(prefix="/cart", tags=["cart"])


async def _build_cart(user: User) -> CartRead:
    items = await CartItem.filter(user=user).prefetch_related("product")
    item_reads = [
        CartItemRead(
            product_id=item.product.id,
            name=item.product.name,
            price=item.product.price,
            image_url=item.product.image_url,
            quantity=item.quantity,
            stock_quantity=item.product.stock_quantity,
            line_total=item.product.price * item.quantity,
        )
        for item in items
    ]
    return CartRead(
        items=item_reads,
        total=sum((i.line_total for i in item_reads), Decimal("0")),
        item_count=sum(i.quantity for i in item_reads),
    )


@router.get("", response_model=CartRead)
async def get_cart(current_user: User = Depends(get_current_user)) -> CartRead:
    return await _build_cart(current_user)


@router.post("/items", response_model=CartRead)
async def add_item(payload: CartItemAdd, current_user: User = Depends(get_current_user)) -> CartRead:
    product = await Product.get_or_none(id=payload.product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    existing = await CartItem.get_or_none(user=current_user, product=product)
    new_quantity = (existing.quantity if existing else 0) + payload.quantity
    if new_quantity > product.stock_quantity:
        raise HTTPException(status_code=400, detail="Not enough stock available")

    if existing:
        existing.quantity = new_quantity
        await existing.save()
    else:
        await CartItem.create(user=current_user, product=product, quantity=new_quantity)

    return await _build_cart(current_user)


@router.put("/items/{product_id}", response_model=CartRead)
async def update_item(
    product_id: int, payload: CartItemUpdate, current_user: User = Depends(get_current_user)
) -> CartRead:
    item = await CartItem.get_or_none(user=current_user, product_id=product_id).prefetch_related("product")
    if item is None:
        raise HTTPException(status_code=404, detail="Item not in cart")
    if payload.quantity > item.product.stock_quantity:
        raise HTTPException(status_code=400, detail="Not enough stock available")

    item.quantity = payload.quantity
    await item.save()
    return await _build_cart(current_user)


@router.delete("/items/{product_id}", response_model=CartRead)
async def remove_item(product_id: int, current_user: User = Depends(get_current_user)) -> CartRead:
    deleted = await CartItem.filter(user=current_user, product_id=product_id).delete()
    if not deleted:
        raise HTTPException(status_code=404, detail="Item not in cart")
    return await _build_cart(current_user)

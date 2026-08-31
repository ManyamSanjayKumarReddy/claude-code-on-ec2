from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query
from tortoise.expressions import Q

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductPage, ProductRead, ProductUpdate

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=ProductPage)
async def list_products(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, max_length=200),
    min_price: Decimal | None = Query(default=None, ge=0),
    max_price: Decimal | None = Query(default=None, ge=0),
    in_stock: bool | None = Query(default=None),
) -> ProductPage:
    qs = Product.all()
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(description__icontains=search))
    if min_price is not None:
        qs = qs.filter(price__gte=min_price)
    if max_price is not None:
        qs = qs.filter(price__lte=max_price)
    if in_stock is True:
        qs = qs.filter(stock_quantity__gt=0)
    elif in_stock is False:
        qs = qs.filter(stock_quantity=0)

    total = await qs.count()
    offset = (page - 1) * page_size
    items = await qs.offset(offset).limit(page_size)
    return ProductPage(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=ProductRead, status_code=201)
async def create_product(payload: ProductCreate) -> Product:
    return await Product.create(**payload.model_dump())


@router.get("/{product_id}", response_model=ProductRead)
async def get_product(product_id: int) -> Product:
    product = await Product.get_or_none(id=product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.put("/{product_id}", response_model=ProductRead)
async def update_product(product_id: int, payload: ProductUpdate) -> Product:
    product = await Product.get_or_none(id=product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    product.update_from_dict(payload.model_dump())
    await product.save()
    return product


@router.delete("/{product_id}", status_code=204)
async def delete_product(product_id: int) -> None:
    deleted_count = await Product.filter(id=product_id).delete()
    if not deleted_count:
        raise HTTPException(status_code=404, detail="Product not found")

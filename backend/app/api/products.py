from fastapi import APIRouter, HTTPException

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductRead])
async def list_products() -> list[Product]:
    return await Product.all()


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

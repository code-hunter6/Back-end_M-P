from decimal import Decimal
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import product as product_crud
from app.db.session import get_db
from app.schemas.product import ProductDetail, ProductListItem, ProductListResponse

router = APIRouter(prefix="/products", tags=["products"])

SortBy = Literal["price_asc", "price_desc", "rating"]


@router.get("", response_model=ProductListResponse)
async def list_products(
    db: Annotated[AsyncSession, Depends(get_db)],
    search: Annotated[str | None, Query(max_length=120)] = None,
    category: Annotated[str | None, Query(max_length=140)] = None,
    min_price: Annotated[Decimal | None, Query(alias="minPrice", ge=0)] = None,
    max_price: Annotated[Decimal | None, Query(alias="maxPrice", ge=0)] = None,
    in_stock_only: Annotated[bool, Query(alias="inStockOnly")] = False,
    sort_by: Annotated[SortBy | None, Query(alias="sortBy")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 24,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ProductListResponse:
    """Query aliases match the frontend's productService filter keys exactly."""
    products, total = await product_crud.list_products(
        db,
        search=search,
        category_slug=category,
        min_price=min_price,
        max_price=max_price,
        in_stock_only=in_stock_only,
        sort_by=sort_by,
        limit=limit,
        offset=offset,
    )
    return ProductListResponse(
        items=[product_crud.to_list_item(p) for p in products], total=total
    )


@router.get("/featured", response_model=list[ProductListItem])
async def featured_products(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=20)] = 3,
) -> list[ProductListItem]:
    # Declared before /{slug} so "featured" isn't swallowed as a slug.
    products = await product_crud.list_featured(db, limit=limit)
    return [product_crud.to_list_item(p) for p in products]


@router.get("/{slug}", response_model=ProductDetail)
async def product_detail(
    slug: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProductDetail:
    product = await product_crud.get_by_slug(db, slug)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
        )
    return product_crud.to_detail(product)

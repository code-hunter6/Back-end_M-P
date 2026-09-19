import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.product import Category, Product
from app.schemas.product import (
    ProductDetail,
    ProductListItem,
    SupplierOut,
    VariantsOut,
)

_DETAIL_LOADERS = (
    selectinload(Product.images),
    selectinload(Product.variants),
    selectinload(Product.reviews),
)


async def list_categories(db: AsyncSession) -> list[Category]:
    result = await db.execute(select(Category).order_by(Category.name))
    return list(result.scalars().all())


async def list_products(
    db: AsyncSession,
    *,
    search: str | None = None,
    category_slug: str | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    in_stock_only: bool = False,
    sort_by: str | None = None,
    limit: int = 24,
    offset: int = 0,
) -> tuple[list[Product], int]:
    stmt = select(Product).where(Product.is_active.is_(True))

    if search:
        # ilike with bound parameters — SQLAlchemy parameterizes this, so the
        # user's input can never be interpreted as SQL.
        pattern = f"%{search.strip()}%"
        stmt = stmt.where(Product.title.ilike(pattern) | Product.brand.ilike(pattern))

    if category_slug:
        stmt = stmt.join(Category).where(Category.slug == category_slug)

    if min_price is not None:
        stmt = stmt.where(Product.price >= min_price)

    if max_price is not None:
        stmt = stmt.where(Product.price <= max_price)

    if in_stock_only:
        stmt = stmt.where(Product.stock_count > 0)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    sort_map = {
        "price_asc": Product.price.asc(),
        "price_desc": Product.price.desc(),
        "rating": Product.rating.desc(),
    }
    stmt = stmt.order_by(sort_map.get(sort_by or "", Product.created_at.desc()))
    stmt = stmt.options(selectinload(Product.images)).limit(limit).offset(offset)

    result = await db.execute(stmt)
    return list(result.scalars().unique().all()), total


async def get_by_slug(db: AsyncSession, slug: str) -> Product | None:
    stmt = (
        select(Product)
        .where(Product.slug == slug, Product.is_active.is_(True))
        .options(*_DETAIL_LOADERS)
    )
    result = await db.execute(stmt)
    product = result.scalars().unique().one_or_none()
    if product is None:
        return None
    # Reviews' photos are a second hop; load them explicitly.
    for review in product.reviews:
        await db.refresh(review, ["photos"])
    return product


async def get_by_id(db: AsyncSession, product_id: uuid.UUID) -> Product | None:
    result = await db.execute(
        select(Product).where(Product.id == product_id, Product.is_active.is_(True))
    )
    return result.scalar_one_or_none()


async def list_featured(db: AsyncSession, limit: int = 3) -> list[Product]:
    stmt = (
        select(Product)
        .where(Product.is_active.is_(True), Product.is_featured.is_(True))
        .options(selectinload(Product.images))
        .order_by(Product.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().unique().all())


# --- serialization helpers -------------------------------------------------


def to_list_item(product: Product) -> ProductListItem:
    return ProductListItem(
        id=product.id,
        slug=product.slug,
        title=product.title,
        brand=product.brand,
        price=product.price,
        compare_at_price=product.compare_at_price,
        currency=product.currency,
        rating=product.rating,
        review_count=product.review_count,
        in_stock=product.in_stock,
        stock_count=product.stock_count,
        images=[img.url for img in product.images],
    )


def to_detail(product: Product) -> ProductDetail:
    colors = [v.option_value for v in product.variants if v.option_name == "color"]
    sizes = [v.option_value for v in product.variants if v.option_name == "size"]

    return ProductDetail(
        **to_list_item(product).model_dump(by_alias=False),
        description=product.description,
        estimated_delivery=product.estimated_delivery,
        variants=VariantsOut(color=colors or None, size=sizes or None),
        supplier=SupplierOut(
            id=product.supplier_id, ships_from=product.supplier_ships_from
        ),
        reviews=[
            {
                "id": r.id,
                "author": r.author,
                "rating": r.rating,
                "comment": r.comment,
                "photos": [p.url for p in r.photos],
                "date": r.review_date,
            }
            for r in product.reviews
        ],
    )

import uuid
from datetime import date
from decimal import Decimal

from pydantic import Field

from app.schemas.common import CamelModel


class CategoryOut(CamelModel):
    id: uuid.UUID
    name: str
    slug: str
    image: str | None = None


class ReviewOut(CamelModel):
    id: uuid.UUID
    author: str
    rating: int
    comment: str | None = None
    photos: list[str] = Field(default_factory=list)
    date: date | None = None


class VariantsOut(CamelModel):
    """Matches the frontend's product.variants = { color: [...] | null, size: ... }."""

    color: list[str] | None = None
    size: list[str] | None = None


class SupplierOut(CamelModel):
    id: str | None = None
    ships_from: str | None = None


class ProductListItem(CamelModel):
    id: uuid.UUID
    slug: str
    title: str
    brand: str | None = None
    price: Decimal
    compare_at_price: Decimal | None = None
    currency: str
    rating: Decimal
    review_count: int
    in_stock: bool
    stock_count: int
    images: list[str] = Field(default_factory=list)


class ProductDetail(ProductListItem):
    description: str | None = None
    estimated_delivery: str | None = None
    variants: VariantsOut
    supplier: SupplierOut
    reviews: list[ReviewOut] = Field(default_factory=list)


class ProductListResponse(CamelModel):
    items: list[ProductListItem]
    total: int

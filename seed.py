"""
Seeds the catalog with the single product the frontend expects.

Run once after migrations:
    python -m app.seed

Safe to re-run: it skips seeding if the product slug already exists.
"""

import asyncio
from datetime import date
from decimal import Decimal

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.product import (
    Category,
    Product,
    ProductImage,
    ProductVariant,
    Review,
    ReviewPhoto,
)

PRODUCT_SLUG = "wireless-earbuds-pro"


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        existing = await db.execute(select(Product).where(Product.slug == PRODUCT_SLUG))
        if existing.scalar_one_or_none() is not None:
            print(f"Product '{PRODUCT_SLUG}' already exists — nothing to seed.")
            return

        category = Category(
            name="Electronics", slug="electronics", image="/mock/cat-electronics.jpg"
        )

        product = Product(
            slug=PRODUCT_SLUG,
            title="Wireless Earbuds Pro",
            brand="SoundWave",
            description=(
                "Immersive sound, active noise cancellation, and 30h battery life "
                "packed into a compact charging case."
            ),
            price=Decimal("29.99"),
            compare_at_price=Decimal("59.99"),
            currency="USD",
            rating=Decimal("4.6"),
            review_count=812,
            stock_count=6,
            is_active=True,
            is_featured=True,
            estimated_delivery="7-12 Business Days",
            supplier_id="sup_aliexpress_88x",
            supplier_ships_from="CN",
            category=category,
        )

        for position, url in enumerate(
            [
                "/mock/earbuds-1.jpg",
                "/mock/earbuds-2.jpg",
                "/mock/earbuds-3.jpg",
                "/mock/earbuds-4.jpg",
            ]
        ):
            product.images.append(ProductImage(url=url, position=position))

        for position, color in enumerate(["Black", "White", "Blue"]):
            product.variants.append(
                ProductVariant(option_name="color", option_value=color, position=position)
            )

        review_one = Review(
            author="Farhana K.",
            rating=5,
            comment="Sound quality is amazing for the price. Battery lasts all day.",
            review_date=date(2026, 7, 14),
        )
        review_one.photos.append(ReviewPhoto(url="/mock/review-1.jpg"))

        review_two = Review(
            author="Rakib H.",
            rating=4,
            comment="Good bass, case a bit bulky but overall happy with the purchase.",
            review_date=date(2026, 6, 30),
        )

        product.reviews.extend([review_one, review_two])

        db.add(product)
        await db.commit()
        print(f"Seeded product '{PRODUCT_SLUG}' successfully.")


if __name__ == "__main__":
    asyncio.run(seed())

import secrets
import uuid
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderItem, OrderStatus, TrackingEvent
from app.models.product import Product
from app.schemas.order import CreateOrderRequest

FREE_SHIPPING_THRESHOLD = Decimal("30.00")
FLAT_SHIPPING_FEE = Decimal("4.99")

TRACKING_STEPS = [
    ("placed", "Order Placed"),
    ("shipped", "Shipped from Warehouse"),
    ("in_transit", "In Transit"),
    ("out_for_delivery", "Out for Delivery"),
    ("delivered", "Delivered"),
]


def _generate_order_number() -> str:
    return f"ORD-{secrets.token_hex(6).upper()}"


def _generate_tracking_id() -> str:
    # Random, not sequential: a sequential ID would let anyone enumerate
    # other customers' orders on the public tracking endpoint.
    return f"TRK{secrets.token_hex(8).upper()}"


async def create_order(
    db: AsyncSession, *, payload: CreateOrderRequest, user_id: uuid.UUID | None
) -> Order:
    product_ids = [item.product_id for item in payload.items]
    result = await db.execute(
        select(Product).where(Product.id.in_(product_ids), Product.is_active.is_(True))
    )
    products = {p.id: p for p in result.scalars().all()}

    missing = [str(pid) for pid in product_ids if pid not in products]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product(s) unavailable: {', '.join(missing)}",
        )

    subtotal = Decimal("0.00")
    order_items: list[OrderItem] = []

    for item in payload.items:
        product = products[item.product_id]

        if product.stock_count < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Not enough stock for '{product.title}'. "
                f"Only {product.stock_count} left.",
            )

        unit_price = Decimal(str(product.price))
        subtotal += unit_price * item.quantity

        variant = item.variant or {}
        order_items.append(
            OrderItem(
                product_id=product.id,
                title=product.title,
                unit_price=unit_price,
                quantity=item.quantity,
                variant_color=variant.get("color"),
                variant_size=variant.get("size"),
            )
        )

        product.stock_count -= item.quantity

    shipping_fee = (
        Decimal("0.00") if subtotal > FREE_SHIPPING_THRESHOLD else FLAT_SHIPPING_FEE
    )
    total = subtotal + shipping_fee

    address = payload.shipping_address
    order = Order(
        order_number=_generate_order_number(),
        tracking_id=_generate_tracking_id(),
        user_id=user_id,
        status=OrderStatus.placed,
        payment_method=payload.payment_method,
        subtotal=subtotal,
        shipping_fee=shipping_fee,
        total=total,
        ship_full_name=address.full_name,
        ship_phone=address.phone,
        ship_line1=address.line1,
        ship_city=address.city,
        ship_postal_code=address.postal_code,
        ship_country=address.country,
        items=order_items,
    )

    # Seed the full timeline; only the first step is marked complete.
    from datetime import datetime, timezone

    for position, (key, label) in enumerate(TRACKING_STEPS):
        order.events.append(
            TrackingEvent(
                key=key,
                label=label,
                position=position,
                occurred_at=datetime.now(timezone.utc) if position == 0 else None,
            )
        )

    db.add(order)
    await db.commit()
    await db.refresh(order, ["items", "events"])
    return order


async def get_by_tracking_id(db: AsyncSession, tracking_id: str) -> Order | None:
    stmt = (
        select(Order)
        .where(Order.tracking_id == tracking_id.strip().upper())
        .options(selectinload(Order.events))
    )
    result = await db.execute(stmt)
    return result.scalars().unique().one_or_none()

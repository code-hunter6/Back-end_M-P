from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_optional
from app.crud import order as order_crud
from app.db.session import get_db
from app.models.user import User
from app.schemas.order import (
    CreateOrderRequest,
    CreateOrderResponse,
    TrackingResponse,
    TrackingStepOut,
)
from app.utils.limiter import limiter

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=CreateOrderResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_order(
    request: Request,
    payload: CreateOrderRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
) -> CreateOrderResponse:
    """
    Guests may order; if a valid token is present the order is linked to that user.
    All money is computed server-side inside crud.order.create_order.
    """
    order = await order_crud.create_order(
        db, payload=payload, user_id=current_user.id if current_user else None
    )
    return CreateOrderResponse(
        order_id=order.order_number,
        status=order.status.value,
        tracking_id=order.tracking_id,
        total=order.total,
        currency=order.currency,
    )


@router.get("/track/{tracking_id}", response_model=TrackingResponse)
@limiter.limit("30/minute")
async def track_order(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    tracking_id: Annotated[str, Path(min_length=6, max_length=40)],
) -> TrackingResponse:
    """
    Public on purpose (customers track without logging in), so it deliberately
    returns only shipping progress — never the address, contact details, totals,
    or line items. Tracking IDs are random to prevent enumeration, and the
    endpoint is rate limited against brute-force guessing.
    """
    order = await order_crud.get_by_tracking_id(db, tracking_id)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No order found for this tracking ID.",
        )

    return TrackingResponse(
        tracking_id=order.tracking_id,
        carrier=order.carrier,
        current_status=order.status.value,
        steps=[
            TrackingStepOut(
                key=event.key,
                label=event.label,
                date=event.occurred_at.date() if event.occurred_at else None,
                done=event.done,
            )
            for event in order.events
        ],
    )

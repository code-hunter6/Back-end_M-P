import re
import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.models.order import PaymentMethod
from app.schemas.common import CamelModel

PHONE_RE = re.compile(r"^[+]?[\d\s-]{7,20}$")


def _clean_text(value: str) -> str:
    """
    Strip angle brackets and collapse whitespace on free-text address fields.
    React escapes on render, but this keeps stored data clean for any other
    consumer (emails, PDF invoices, admin panels) that isn't auto-escaping.
    """
    cleaned = re.sub(r"[<>]", "", value).strip()
    return re.sub(r"\s+", " ", cleaned)


class CartItemIn(CamelModel):
    product_id: uuid.UUID
    quantity: int = Field(ge=1, le=100)
    variant: dict[str, str | None] | None = None


class ShippingAddressIn(CamelModel):
    full_name: str = Field(min_length=2, max_length=120)
    phone: str = Field(min_length=7, max_length=20)
    line1: str = Field(min_length=3, max_length=255)
    city: str = Field(min_length=2, max_length=120)
    postal_code: str = Field(min_length=2, max_length=30)
    country: str = Field(min_length=2, max_length=120)

    @field_validator("full_name", "line1", "city", "postal_code", "country")
    @classmethod
    def sanitize(cls, v: str) -> str:
        return _clean_text(v)

    @field_validator("phone")
    @classmethod
    def valid_phone(cls, v: str) -> str:
        cleaned = v.strip()
        if not PHONE_RE.match(cleaned):
            raise ValueError("Enter a valid phone number.")
        return cleaned


class CreateOrderRequest(CamelModel):
    """
    Note there is deliberately no `totals` field. The frontend sends one, but
    it is ignored — the server recomputes every amount from the product table.
    Accepting client-supplied prices would let anyone buy at any price.
    """

    items: list[CartItemIn] = Field(min_length=1, max_length=50)
    shipping_address: ShippingAddressIn
    payment_method: PaymentMethod


class CreateOrderResponse(CamelModel):
    order_id: str
    status: str
    tracking_id: str
    total: Decimal
    currency: str


class TrackingStepOut(CamelModel):
    key: str
    label: str
    date: date | None = None
    done: bool


class TrackingResponse(CamelModel):
    tracking_id: str
    carrier: str | None = None
    current_status: str
    steps: list[TrackingStepOut]


class MessageResponse(BaseModel):
    message: str

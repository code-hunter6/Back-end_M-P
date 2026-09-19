"""Import every model here so Alembic autogenerate sees the full metadata."""

from app.models.order import (  # noqa: F401
    Order,
    OrderItem,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
    TrackingEvent,
)
from app.models.product import (  # noqa: F401
    Category,
    Product,
    ProductImage,
    ProductVariant,
    Review,
    ReviewPhoto,
)
from app.models.user import User  # noqa: F401

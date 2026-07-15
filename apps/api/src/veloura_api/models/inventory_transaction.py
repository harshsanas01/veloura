import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from veloura_api.database import Base
from veloura_api.models.base import TimestampMixin, UUIDPKMixin


class InventoryChangeReason(str, enum.Enum):
    ORDER_PLACED = "order_placed"
    ORDER_CANCELLED = "order_cancelled"
    RETURN = "return"
    ADMIN_ADJUSTMENT = "admin_adjustment"


class InventoryTransaction(Base, UUIDPKMixin, TimestampMixin):
    """Immutable audit log of every stock change, so inventory can always be
    reconstructed and explained rather than trusted blindly."""

    __tablename__ = "inventory_transactions"

    variant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=False
    )
    change_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    resulting_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[InventoryChangeReason] = mapped_column(
        Enum(InventoryChangeReason, name="inventory_change_reason"), nullable=False
    )
    order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="SET NULL"), nullable=True
    )
    admin_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    variant = relationship("ProductVariant")

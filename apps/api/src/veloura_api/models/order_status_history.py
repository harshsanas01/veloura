import uuid

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from veloura_api.database import Base
from veloura_api.models.base import TimestampMixin, UUIDPKMixin
from veloura_api.models.order import OrderStatus


class OrderStatusHistory(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "order_status_history"

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus, name="order_status"), nullable=False)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    order = relationship("Order", back_populates="status_history")

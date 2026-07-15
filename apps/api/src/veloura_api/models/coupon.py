import datetime
import enum
import uuid

from sqlalchemy import ARRAY, Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from veloura_api.database import Base
from veloura_api.models.base import TimestampMixin, UUIDPKMixin


class DiscountType(str, enum.Enum):
    FIXED = "fixed"
    PERCENTAGE = "percentage"


class Coupon(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "coupons"

    code: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    discount_type: Mapped[DiscountType] = mapped_column(
        Enum(DiscountType, name="coupon_discount_type"), nullable=False
    )
    discount_value: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    free_shipping: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    min_order_value: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    max_discount: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    starts_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    usage_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    per_user_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    applicable_categories: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    applicable_products: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), default=list, nullable=False
    )

    redemptions = relationship("CouponRedemption", back_populates="coupon", cascade="all, delete-orphan")


class CouponRedemption(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "coupon_redemptions"

    coupon_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("coupons.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    amount_discounted: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    coupon = relationship("Coupon", back_populates="redemptions")

import enum
import uuid

from sqlalchemy import Boolean, CheckConstraint, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from veloura_api.database import Base
from veloura_api.models.base import TimestampMixin, UUIDPKMixin


class FitFeedback(str, enum.Enum):
    RUNS_SMALL = "runs_small"
    TRUE_TO_SIZE = "true_to_size"
    RUNS_LARGE = "runs_large"


class Review(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("product_id", "user_id", name="uq_review_product_user"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_review_rating_range"),
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    fit_feedback: Mapped[FitFeedback | None] = mapped_column(
        Enum(FitFeedback, name="review_fit_feedback"), nullable=True
    )
    size_purchased: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_verified_purchase: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    product = relationship("Product")
    user = relationship("User")
    helpfulness_votes = relationship(
        "ReviewHelpfulness", back_populates="review", cascade="all, delete-orphan"
    )


class ReviewHelpfulness(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "review_helpfulness"
    __table_args__ = (UniqueConstraint("review_id", "user_id", name="uq_review_helpfulness_user"),)

    review_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    review = relationship("Review", back_populates="helpfulness_votes")

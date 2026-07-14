import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from veloura_api.database import Base
from veloura_api.models.base import TimestampMixin, UUIDPKMixin


class FeedbackRating(str, enum.Enum):
    LIKE = "like"
    DISLIKE = "dislike"


class RecommendationFeedback(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "recommendation_feedback"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    outfit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("outfits.id", ondelete="CASCADE"), nullable=False
    )
    rating: Mapped[FeedbackRating] = mapped_column(
        Enum(FeedbackRating, name="feedback_rating"), nullable=False
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

import uuid

from sqlalchemy import ARRAY, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from veloura_api.database import Base
from veloura_api.models.base import TimestampMixin, UUIDPKMixin


class StyleProfile(Base, UUIDPKMixin, TimestampMixin):
    """Lightweight, evolving snapshot of a user's style preferences, used to
    personalize the AI stylist and (later) deterministic recommendations."""

    __tablename__ = "style_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    gender_presentation: Mapped[str | None] = mapped_column(String(20), nullable=True)
    preferred_colors: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    disliked_colors: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    preferred_styles: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    favorite_occasions: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    preferred_brands: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    sizes: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    budget_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    budget_max: Mapped[int | None] = mapped_column(Integer, nullable=True)

    user = relationship("User", back_populates="style_profile")

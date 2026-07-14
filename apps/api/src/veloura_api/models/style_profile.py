import uuid

from sqlalchemy import ARRAY, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from veloura_api.database import Base
from veloura_api.models.base import TimestampMixin, UUIDPKMixin


class StyleProfile(Base, UUIDPKMixin, TimestampMixin):
    """Lightweight, evolving snapshot of a user's style preferences."""

    __tablename__ = "style_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    preferred_colors: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    preferred_styles: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    sizes: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    user = relationship("User", back_populates="style_profile")

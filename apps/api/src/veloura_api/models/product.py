import enum
import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import ARRAY, Boolean, ForeignKey, Integer, Numeric, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from veloura_api.database import Base
from veloura_api.models.base import TimestampMixin, UUIDPKMixin

EMBEDDING_DIM = 1536


class Gender(str, enum.Enum):
    MEN = "men"
    WOMEN = "women"
    UNISEX = "unisex"


class Product(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "products"

    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    brand: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(2000), nullable=False)
    short_description: Mapped[str] = mapped_column(String(300), nullable=False)

    gender: Mapped[Gender] = mapped_column(SAEnum(Gender, name="product_gender"), nullable=False, index=True)
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False
    )

    base_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    sale_price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

    material: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    care_instructions: Mapped[str] = mapped_column(String(500), nullable=False)

    occasion_tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    style_tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    season_tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)

    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)

    category = relationship("Category", back_populates="products")
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")

    @property
    def effective_price(self) -> float:
        return float(self.sale_price) if self.sale_price else float(self.base_price)


class ProductVariant(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "product_variants"

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    sku: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    size: Mapped[str] = mapped_column(String(20), nullable=False)
    color_name: Mapped[str] = mapped_column(String(60), nullable=False)
    color_hex: Mapped[str] = mapped_column(String(7), nullable=False)
    inventory_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)

    product = relationship("Product", back_populates="variants")

import uuid
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from veloura_api.models.product import Gender
from veloura_api.schemas.category import CategoryOut


class ProductVariantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sku: str
    size: str
    color_name: str
    color_hex: str
    inventory_quantity: int
    image_url: str

    @property
    def in_stock(self) -> bool:
        return self.inventory_quantity > 0


class ProductListItemOut(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    brand: str
    gender: Gender
    category_slug: str
    category_name: str
    base_price: float
    sale_price: float | None
    effective_price: float
    primary_image: str
    available_colors: list[str]
    is_featured: bool
    in_stock: bool


class ProductOut(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    brand: str
    description: str
    short_description: str
    gender: Gender
    category: CategoryOut
    base_price: float
    sale_price: float | None
    effective_price: float
    material: str
    care_instructions: str
    occasion_tags: list[str]
    style_tags: list[str]
    season_tags: list[str]
    is_featured: bool
    variants: list[ProductVariantOut]
    available_sizes: list[str]
    available_colors: list[dict]


class SortOption(str, Enum):
    NEWEST = "newest"
    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"
    FEATURED = "featured"
    NAME_ASC = "name_asc"


class ProductListResponse(BaseModel):
    items: list[ProductListItemOut]
    total: int
    page: int
    page_size: int
    total_pages: int


class ProductFilterParams(BaseModel):
    q: str | None = None
    gender: Gender | None = None
    category: list[str] | None = None
    size: list[str] | None = None
    color: list[str] | None = None
    min_price: float | None = Field(default=None, ge=0)
    max_price: float | None = Field(default=None, ge=0)
    sort: SortOption = SortOption.NEWEST
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=12, ge=1, le=48)

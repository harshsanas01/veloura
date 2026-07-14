import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from veloura_api.models.order import OrderStatus
from veloura_api.models.product import Gender


class AdminVariantInput(BaseModel):
    sku: str
    size: str
    color_name: str
    color_hex: str
    inventory_quantity: int = Field(ge=0)
    image_url: str


class AdminVariantUpdate(BaseModel):
    size: str | None = None
    color_name: str | None = None
    color_hex: str | None = None
    inventory_quantity: int | None = Field(default=None, ge=0)
    image_url: str | None = None


class AdminVariantOut(BaseModel):
    id: uuid.UUID
    sku: str
    size: str
    color_name: str
    color_hex: str
    inventory_quantity: int
    image_url: str


class AdminProductCreate(BaseModel):
    name: str
    brand: str
    description: str
    short_description: str
    gender: Gender
    category_id: uuid.UUID
    base_price: float = Field(gt=0)
    sale_price: float | None = Field(default=None, gt=0)
    material: str
    care_instructions: str
    occasion_tags: list[str] = Field(default_factory=list)
    style_tags: list[str] = Field(default_factory=list)
    season_tags: list[str] = Field(default_factory=list)
    is_featured: bool = False
    is_active: bool = True
    variants: list[AdminVariantInput] = Field(default_factory=list)


class AdminProductUpdate(BaseModel):
    name: str | None = None
    brand: str | None = None
    description: str | None = None
    short_description: str | None = None
    gender: Gender | None = None
    category_id: uuid.UUID | None = None
    base_price: float | None = Field(default=None, gt=0)
    sale_price: float | None = Field(default=None, gt=0)
    material: str | None = None
    care_instructions: str | None = None
    occasion_tags: list[str] | None = None
    style_tags: list[str] | None = None
    season_tags: list[str] | None = None
    is_featured: bool | None = None
    is_active: bool | None = None


class AdminProductOut(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    brand: str
    gender: Gender
    category_id: uuid.UUID
    base_price: float
    sale_price: float | None
    is_featured: bool
    is_active: bool
    variants: list[AdminVariantOut]
    created_at: datetime


class AdminOrderItemOut(BaseModel):
    product_name: str
    variant_size: str
    variant_color: str
    unit_price: float
    quantity: int


class AdminOrderOut(BaseModel):
    id: uuid.UUID
    order_number: str
    status: OrderStatus
    customer_email: str
    total: float
    items: list[AdminOrderItemOut]
    created_at: datetime

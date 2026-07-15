import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from veloura_api.models.coupon import DiscountType
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


class AdminProductListResponse(BaseModel):
    items: list[AdminProductOut]
    total: int
    page: int
    page_size: int
    total_pages: int


class AdminOrderListResponse(BaseModel):
    items: list[AdminOrderOut]
    total: int
    page: int
    page_size: int
    total_pages: int


class AdminCustomerOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    order_count: int
    total_spent: float
    created_at: datetime


class AdminCustomerListResponse(BaseModel):
    items: list[AdminCustomerOut]
    total: int
    page: int
    page_size: int
    total_pages: int


class InventoryAdjustmentRequest(BaseModel):
    delta: int
    reason: str = Field(min_length=1, max_length=500)


class BestSellingProductOut(BaseModel):
    product_id: uuid.UUID
    name: str
    slug: str
    units_sold: int


class TopCategoryOut(BaseModel):
    category_name: str
    category_slug: str
    revenue: float


class AdminDashboardOut(BaseModel):
    total_revenue: float
    total_orders: int
    total_customers: int
    average_order_value: float
    low_stock_variant_count: int
    out_of_stock_variant_count: int
    best_selling_products: list[BestSellingProductOut]
    recent_orders: list[AdminOrderOut]
    top_categories: list[TopCategoryOut]


class AdminCouponCreate(BaseModel):
    code: str = Field(min_length=1, max_length=40)
    discount_type: DiscountType
    discount_value: float = Field(ge=0)
    free_shipping: bool = False
    min_order_value: float | None = Field(default=None, ge=0)
    max_discount: float | None = Field(default=None, ge=0)
    starts_at: datetime | None = None
    expires_at: datetime | None = None
    is_active: bool = True
    usage_limit: int | None = Field(default=None, ge=1)
    per_user_limit: int | None = Field(default=None, ge=1)
    applicable_categories: list[str] = Field(default_factory=list)
    applicable_products: list[uuid.UUID] = Field(default_factory=list)


class AdminCouponUpdate(BaseModel):
    discount_type: DiscountType | None = None
    discount_value: float | None = Field(default=None, ge=0)
    free_shipping: bool | None = None
    min_order_value: float | None = Field(default=None, ge=0)
    max_discount: float | None = Field(default=None, ge=0)
    starts_at: datetime | None = None
    expires_at: datetime | None = None
    is_active: bool | None = None
    usage_limit: int | None = Field(default=None, ge=1)
    per_user_limit: int | None = Field(default=None, ge=1)
    applicable_categories: list[str] | None = None
    applicable_products: list[uuid.UUID] | None = None


class AdminCouponOut(BaseModel):
    id: uuid.UUID
    code: str
    discount_type: DiscountType
    discount_value: float
    free_shipping: bool
    min_order_value: float | None
    max_discount: float | None
    starts_at: datetime | None
    expires_at: datetime | None
    is_active: bool
    usage_limit: int | None
    per_user_limit: int | None
    applicable_categories: list[str]
    applicable_products: list[uuid.UUID]
    total_redemptions: int
    created_at: datetime

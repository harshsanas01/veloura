import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from veloura_api.models.order import OrderStatus


class ShippingAddressInput(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    line1: str = Field(min_length=1, max_length=255)
    line2: str | None = None
    city: str = Field(min_length=1, max_length=120)
    state: str = Field(min_length=1, max_length=120)
    postal_code: str = Field(min_length=1, max_length=20)
    country: str = Field(min_length=1, max_length=120)
    phone: str = Field(min_length=1, max_length=30)


class CreateOrderRequest(BaseModel):
    shipping_address: ShippingAddressInput
    coupon_code: str | None = Field(default=None, max_length=40)
    customer_notes: str | None = Field(default=None, max_length=1000)


class OrderItemOut(BaseModel):
    id: uuid.UUID
    product_name: str
    variant_size: str
    variant_color: str
    unit_price: float
    quantity: int
    line_total: float
    product_slug: str | None = None
    image_url: str | None = None


class OrderStatusHistoryOut(BaseModel):
    status: OrderStatus
    note: str | None
    created_at: datetime


class OrderOut(BaseModel):
    id: uuid.UUID
    order_number: str
    status: OrderStatus
    subtotal: float
    discount_amount: float
    shipping_cost: float
    tax: float
    total: float
    coupon_code: str | None
    customer_notes: str | None
    shipping_address: dict
    items: list[OrderItemOut]
    status_history: list[OrderStatusHistoryOut]
    can_cancel: bool
    created_at: datetime


class OrderSummaryOut(BaseModel):
    id: uuid.UUID
    order_number: str
    status: OrderStatus
    total: float
    item_count: int
    created_at: datetime


class UpdateOrderStatusRequest(BaseModel):
    status: OrderStatus
    note: str | None = Field(default=None, max_length=500)

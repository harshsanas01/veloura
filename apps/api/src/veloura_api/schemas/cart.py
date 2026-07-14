import uuid

from pydantic import BaseModel, Field


class CartItemVariantOut(BaseModel):
    id: uuid.UUID
    sku: str
    size: str
    color_name: str
    color_hex: str
    image_url: str
    inventory_quantity: int
    product_id: uuid.UUID
    product_name: str
    product_slug: str
    product_brand: str
    unit_price: float


class CartItemOut(BaseModel):
    id: uuid.UUID
    quantity: int
    variant: CartItemVariantOut
    line_total: float


class CartOut(BaseModel):
    id: uuid.UUID
    items: list[CartItemOut]
    subtotal: float
    item_count: int


class AddCartItemRequest(BaseModel):
    variant_id: uuid.UUID
    quantity: int = Field(default=1, ge=1, le=20)


class UpdateCartItemRequest(BaseModel):
    quantity: int = Field(ge=1, le=20)

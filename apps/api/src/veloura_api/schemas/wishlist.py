import uuid

from pydantic import BaseModel


class WishlistItemOut(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    slug: str
    name: str
    brand: str
    primary_image: str
    base_price: float
    sale_price: float | None
    effective_price: float
    on_sale: bool
    in_stock: bool


class WishlistOut(BaseModel):
    items: list[WishlistItemOut]


class AddWishlistItemRequest(BaseModel):
    product_id: uuid.UUID


class MoveWishlistItemToCartRequest(BaseModel):
    variant_id: uuid.UUID
    quantity: int = 1

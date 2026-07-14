import uuid

from pydantic import BaseModel


class WishlistItemOut(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    slug: str
    name: str
    brand: str
    primary_image: str
    effective_price: float
    in_stock: bool


class WishlistOut(BaseModel):
    items: list[WishlistItemOut]


class AddWishlistItemRequest(BaseModel):
    product_id: uuid.UUID

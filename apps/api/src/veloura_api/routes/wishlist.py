import uuid

from fastapi import APIRouter

from veloura_api.dependencies import CurrentUser, DbSession
from veloura_api.schemas.wishlist import AddWishlistItemRequest, WishlistOut
from veloura_api.services.wishlist_service import WishlistService

router = APIRouter(prefix="/wishlist", tags=["wishlist"])


@router.get("", response_model=WishlistOut)
def get_wishlist(current_user: CurrentUser, db: DbSession) -> WishlistOut:
    return WishlistService(db).get_wishlist(current_user.id)


@router.post("/items", response_model=WishlistOut, status_code=201)
def add_item(payload: AddWishlistItemRequest, current_user: CurrentUser, db: DbSession) -> WishlistOut:
    return WishlistService(db).add_item(current_user.id, payload.product_id)


@router.delete("/items/{product_id}", response_model=WishlistOut)
def remove_item(product_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> WishlistOut:
    return WishlistService(db).remove_item(current_user.id, product_id)

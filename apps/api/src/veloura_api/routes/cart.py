import uuid

from fastapi import APIRouter

from veloura_api.dependencies import CurrentUser, DbSession
from veloura_api.schemas.cart import (
    AddCartItemRequest,
    ApplyCouponRequest,
    CartOut,
    UpdateCartItemRequest,
)
from veloura_api.services.cart_service import CartService

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("", response_model=CartOut)
def get_cart(current_user: CurrentUser, db: DbSession) -> CartOut:
    return CartService(db).get_cart(current_user.id)


@router.post("/items", response_model=CartOut, status_code=201)
def add_item(payload: AddCartItemRequest, current_user: CurrentUser, db: DbSession) -> CartOut:
    return CartService(db).add_item(current_user.id, payload.variant_id, payload.quantity)


@router.patch("/items/{item_id}", response_model=CartOut)
def update_item(
    item_id: uuid.UUID, payload: UpdateCartItemRequest, current_user: CurrentUser, db: DbSession
) -> CartOut:
    return CartService(db).update_item(current_user.id, item_id, payload.quantity)


@router.delete("/items/{item_id}", response_model=CartOut)
def remove_item(item_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> CartOut:
    return CartService(db).remove_item(current_user.id, item_id)


@router.post("/items/{item_id}/move-to-wishlist", response_model=CartOut)
def move_to_wishlist(item_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> CartOut:
    return CartService(db).move_to_wishlist(current_user.id, item_id)


@router.post("/coupon", response_model=CartOut)
def apply_coupon(payload: ApplyCouponRequest, current_user: CurrentUser, db: DbSession) -> CartOut:
    return CartService(db).apply_coupon(current_user.id, payload.code)


@router.delete("/coupon", response_model=CartOut)
def remove_coupon(current_user: CurrentUser, db: DbSession) -> CartOut:
    return CartService(db).remove_coupon(current_user.id)

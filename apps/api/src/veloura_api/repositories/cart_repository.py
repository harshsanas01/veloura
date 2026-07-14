import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from veloura_api.models.cart import Cart, CartItem
from veloura_api.models.product import ProductVariant


class CartRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_or_create_for_user(self, user_id: uuid.UUID) -> Cart:
        cart = self.db.scalar(
            select(Cart)
            .where(Cart.user_id == user_id)
            .options(
                selectinload(Cart.items)
                .joinedload(CartItem.variant)
                .joinedload(ProductVariant.product)
            )
        )
        if cart is None:
            cart = Cart(user_id=user_id)
            self.db.add(cart)
            self.db.commit()
            self.db.refresh(cart)
        return cart

    def get_variant(self, variant_id: uuid.UUID) -> ProductVariant | None:
        return self.db.scalar(
            select(ProductVariant)
            .where(ProductVariant.id == variant_id)
            .options(joinedload(ProductVariant.product))
        )

    def get_item(self, cart_id: uuid.UUID, variant_id: uuid.UUID) -> CartItem | None:
        return self.db.scalar(
            select(CartItem).where(CartItem.cart_id == cart_id, CartItem.variant_id == variant_id)
        )

    def get_item_by_id(self, item_id: uuid.UUID) -> CartItem | None:
        return self.db.scalar(
            select(CartItem)
            .where(CartItem.id == item_id)
            .options(joinedload(CartItem.variant).joinedload(ProductVariant.product))
        )

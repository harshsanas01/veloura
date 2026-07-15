import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from veloura_api.models.product import Product
from veloura_api.models.wishlist import Wishlist, WishlistItem


class WishlistRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_or_create_for_user(self, user_id: uuid.UUID) -> Wishlist:
        wishlist = self.db.scalar(
            select(Wishlist)
            .where(Wishlist.user_id == user_id)
            .options(
                selectinload(Wishlist.items).selectinload(WishlistItem.product).selectinload(Product.variants)
            )
        )
        if wishlist is None:
            wishlist = Wishlist(user_id=user_id)
            self.db.add(wishlist)
            self.db.commit()
            self.db.refresh(wishlist)
        return wishlist

    def get_item(self, wishlist_id: uuid.UUID, product_id: uuid.UUID) -> WishlistItem | None:
        return self.db.scalar(
            select(WishlistItem).where(
                WishlistItem.wishlist_id == wishlist_id, WishlistItem.product_id == product_id
            )
        )

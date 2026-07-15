import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from veloura_api.repositories.product_repository import ProductRepository
from veloura_api.repositories.wishlist_repository import WishlistRepository
from veloura_api.schemas.wishlist import WishlistItemOut, WishlistOut
from veloura_api.services.cart_service import CartService
from veloura_api.services.product_service import PLACEHOLDER_IMAGE


class WishlistService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = WishlistRepository(db)
        self.products = ProductRepository(db)

    def get_wishlist(self, user_id: uuid.UUID) -> WishlistOut:
        wishlist = self.repo.get_or_create_for_user(user_id)
        items = []
        for item in wishlist.items:
            product = item.product
            image = product.variants[0].image_url if product.variants else PLACEHOLDER_IMAGE
            items.append(
                WishlistItemOut(
                    id=item.id,
                    product_id=product.id,
                    slug=product.slug,
                    name=product.name,
                    brand=product.brand,
                    primary_image=image,
                    base_price=float(product.base_price),
                    sale_price=float(product.sale_price) if product.sale_price else None,
                    effective_price=product.effective_price,
                    on_sale=product.sale_price is not None,
                    in_stock=any(v.inventory_quantity > 0 for v in product.variants),
                )
            )
        return WishlistOut(items=items)

    def add_item(self, user_id: uuid.UUID, product_id: uuid.UUID) -> WishlistOut:
        product = self.products.get_by_id(product_id)
        if not product or not product.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
        wishlist = self.repo.get_or_create_for_user(user_id)
        if not self.repo.get_item(wishlist.id, product_id):
            from veloura_api.models.wishlist import WishlistItem

            self.db.add(WishlistItem(wishlist_id=wishlist.id, product_id=product_id))
            self.db.commit()
        return self.get_wishlist(user_id)

    def remove_item(self, user_id: uuid.UUID, product_id: uuid.UUID) -> WishlistOut:
        wishlist = self.repo.get_or_create_for_user(user_id)
        item = self.repo.get_item(wishlist.id, product_id)
        if item:
            self.db.delete(item)
            self.db.commit()
        return self.get_wishlist(user_id)

    def move_to_cart(
        self, user_id: uuid.UUID, product_id: uuid.UUID, variant_id: uuid.UUID, quantity: int
    ) -> WishlistOut:
        wishlist = self.repo.get_or_create_for_user(user_id)
        item = self.repo.get_item(wishlist.id, product_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist item not found.")

        product = self.products.get_by_id(product_id)
        if not product or not any(v.id == variant_id for v in product.variants):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="That size/color isn't available for this product.",
            )

        CartService(self.db).add_item(user_id, variant_id, quantity)
        self.db.delete(item)
        self.db.commit()
        return self.get_wishlist(user_id)

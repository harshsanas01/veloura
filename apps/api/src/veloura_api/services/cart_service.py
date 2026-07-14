import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from veloura_api.models.cart import Cart, CartItem
from veloura_api.repositories.cart_repository import CartRepository
from veloura_api.schemas.cart import CartItemOut, CartItemVariantOut, CartOut


def _to_item_out(item: CartItem) -> CartItemOut:
    variant = item.variant
    product = variant.product
    unit_price = product.effective_price
    return CartItemOut(
        id=item.id,
        quantity=item.quantity,
        variant=CartItemVariantOut(
            id=variant.id,
            sku=variant.sku,
            size=variant.size,
            color_name=variant.color_name,
            color_hex=variant.color_hex,
            image_url=variant.image_url,
            inventory_quantity=variant.inventory_quantity,
            product_id=product.id,
            product_name=product.name,
            product_slug=product.slug,
            product_brand=product.brand,
            unit_price=unit_price,
        ),
        line_total=round(unit_price * item.quantity, 2),
    )


def _to_cart_out(cart: Cart) -> CartOut:
    items = [_to_item_out(i) for i in cart.items]
    return CartOut(
        id=cart.id,
        items=items,
        subtotal=round(sum(i.line_total for i in items), 2),
        item_count=sum(i.quantity for i in items),
    )


class CartService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = CartRepository(db)

    def get_cart(self, user_id: uuid.UUID) -> CartOut:
        cart = self.repo.get_or_create_for_user(user_id)
        return _to_cart_out(cart)

    def add_item(self, user_id: uuid.UUID, variant_id: uuid.UUID, quantity: int) -> CartOut:
        cart = self.repo.get_or_create_for_user(user_id)
        variant = self.repo.get_variant(variant_id)
        if not variant or not variant.product.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product variant not found.")

        existing = self.repo.get_item(cart.id, variant_id)
        desired_quantity = quantity + (existing.quantity if existing else 0)
        if desired_quantity > variant.inventory_quantity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Only {variant.inventory_quantity} left in stock for this size/color.",
            )

        if existing:
            existing.quantity = desired_quantity
        else:
            self.db.add(CartItem(cart_id=cart.id, variant_id=variant_id, quantity=quantity))

        self.db.commit()
        return self.get_cart(user_id)

    def update_item(self, user_id: uuid.UUID, item_id: uuid.UUID, quantity: int) -> CartOut:
        item = self.repo.get_item_by_id(item_id)
        cart = self.repo.get_or_create_for_user(user_id)
        if not item or item.cart_id != cart.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found.")
        if quantity > item.variant.inventory_quantity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Only {item.variant.inventory_quantity} left in stock for this size/color.",
            )
        item.quantity = quantity
        self.db.commit()
        return self.get_cart(user_id)

    def remove_item(self, user_id: uuid.UUID, item_id: uuid.UUID) -> CartOut:
        item = self.repo.get_item_by_id(item_id)
        cart = self.repo.get_or_create_for_user(user_id)
        if not item or item.cart_id != cart.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found.")
        self.db.delete(item)
        self.db.commit()
        return self.get_cart(user_id)

    def clear(self, user_id: uuid.UUID) -> None:
        cart = self.repo.get_or_create_for_user(user_id)
        for item in list(cart.items):
            self.db.delete(item)
        self.db.commit()

import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from veloura_api.models.cart import Cart, CartItem
from veloura_api.repositories.cart_repository import CartRepository
from veloura_api.repositories.wishlist_repository import WishlistRepository
from veloura_api.schemas.cart import CartItemOut, CartItemVariantOut, CartOut
from veloura_api.services.coupon_service import CouponError, CouponService
from veloura_api.services.pricing import calculate_order_totals, free_shipping_remaining


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


class CartService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = CartRepository(db)
        self.wishlist_repo = WishlistRepository(db)
        self.coupons = CouponService(db)

    def _to_cart_out(self, cart: Cart, user_id: uuid.UUID) -> CartOut:
        items = [_to_item_out(i) for i in cart.items]
        subtotal = round(sum(i.line_total for i in items), 2)

        discount_amount = 0.0
        free_shipping = False
        coupon_error: str | None = None
        if cart.coupon_code:
            try:
                application = self.coupons.validate(
                    code=cart.coupon_code, user_id=user_id, items=list(cart.items)
                )
                discount_amount = application.discount_amount
                free_shipping = application.free_shipping
            except CouponError as exc:
                coupon_error = str(exc)

        totals = calculate_order_totals(
            subtotal, discount_amount=discount_amount, free_shipping=free_shipping
        )
        remaining = free_shipping_remaining(subtotal, discount_amount) if not free_shipping else 0.0

        return CartOut(
            id=cart.id,
            items=items,
            subtotal=subtotal,
            item_count=sum(i.quantity for i in items),
            coupon_code=cart.coupon_code if not coupon_error else None,
            coupon_error=coupon_error,
            discount_amount=totals["discount_amount"],
            shipping_estimate=totals["shipping_cost"],
            tax_estimate=totals["tax"],
            estimated_total=totals["total"],
            free_shipping_remaining=remaining,
        )

    def get_cart(self, user_id: uuid.UUID) -> CartOut:
        cart = self.repo.get_or_create_for_user(user_id)
        return self._to_cart_out(cart, user_id)

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

    def move_to_wishlist(self, user_id: uuid.UUID, item_id: uuid.UUID) -> CartOut:
        item = self.repo.get_item_by_id(item_id)
        cart = self.repo.get_or_create_for_user(user_id)
        if not item or item.cart_id != cart.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found.")
        wishlist = self.wishlist_repo.get_or_create_for_user(user_id)
        product_id = item.variant.product_id
        if not self.wishlist_repo.get_item(wishlist.id, product_id):
            from veloura_api.models.wishlist import WishlistItem

            self.db.add(WishlistItem(wishlist_id=wishlist.id, product_id=product_id))
        self.db.delete(item)
        self.db.commit()
        return self.get_cart(user_id)

    def clear(self, user_id: uuid.UUID) -> None:
        cart = self.repo.get_or_create_for_user(user_id)
        for item in list(cart.items):
            self.db.delete(item)
        self.db.commit()

    def apply_coupon(self, user_id: uuid.UUID, code: str) -> CartOut:
        cart = self.repo.get_or_create_for_user(user_id)
        try:
            self.coupons.validate(code=code, user_id=user_id, items=list(cart.items))
        except CouponError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        cart.coupon_code = code.upper()
        self.db.commit()
        return self.get_cart(user_id)

    def remove_coupon(self, user_id: uuid.UUID) -> CartOut:
        cart = self.repo.get_or_create_for_user(user_id)
        cart.coupon_code = None
        self.db.commit()
        return self.get_cart(user_id)

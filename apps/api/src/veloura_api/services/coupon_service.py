import dataclasses
import datetime
import uuid

from sqlalchemy.orm import Session

from veloura_api.models.cart import CartItem
from veloura_api.models.coupon import Coupon, DiscountType
from veloura_api.repositories.coupon_repository import CouponRepository


class CouponError(Exception):
    pass


@dataclasses.dataclass
class CouponApplication:
    coupon: Coupon
    discount_amount: float
    free_shipping: bool


class CouponService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = CouponRepository(db)

    def _eligible_subtotal(self, coupon: Coupon, items: list[CartItem]) -> float:
        if not coupon.applicable_categories and not coupon.applicable_products:
            return sum(item.variant.product.effective_price * item.quantity for item in items)

        total = 0.0
        product_ids = set(coupon.applicable_products or [])
        category_slugs = set(coupon.applicable_categories or [])
        for item in items:
            product = item.variant.product
            matches = product.id in product_ids or (
                product.category and product.category.slug in category_slugs
            )
            if matches:
                total += product.effective_price * item.quantity
        return total

    def validate(self, *, code: str, user_id: uuid.UUID, items: list[CartItem]) -> CouponApplication:
        if not items:
            raise CouponError("Your cart is empty.")

        coupon = self.repo.get_by_code(code)
        if not coupon or not coupon.is_active:
            raise CouponError("This coupon code is not valid.")

        now = datetime.datetime.now(datetime.UTC)
        if coupon.starts_at and coupon.starts_at > now:
            raise CouponError("This coupon isn't active yet.")
        if coupon.expires_at and coupon.expires_at < now:
            raise CouponError("This coupon has expired.")

        if coupon.usage_limit is not None and self.repo.total_redemptions(coupon.id) >= coupon.usage_limit:
            raise CouponError("This coupon has reached its usage limit.")
        if (
            coupon.per_user_limit is not None
            and self.repo.user_redemptions(coupon.id, user_id) >= coupon.per_user_limit
        ):
            raise CouponError("You've already used this coupon the maximum number of times.")

        subtotal = sum(item.variant.product.effective_price * item.quantity for item in items)
        if coupon.min_order_value is not None and subtotal < float(coupon.min_order_value):
            raise CouponError(
                f"This coupon requires a minimum order of ${float(coupon.min_order_value):,.2f}."
            )

        eligible_subtotal = self._eligible_subtotal(coupon, items)
        if eligible_subtotal <= 0:
            raise CouponError("This coupon doesn't apply to any items currently in your cart.")

        if coupon.discount_type == DiscountType.PERCENTAGE:
            discount = eligible_subtotal * (float(coupon.discount_value) / 100)
        else:
            discount = float(coupon.discount_value)

        if coupon.max_discount is not None:
            discount = min(discount, float(coupon.max_discount))
        discount = min(discount, eligible_subtotal)

        return CouponApplication(
            coupon=coupon, discount_amount=round(discount, 2), free_shipping=coupon.free_shipping
        )

    def record_redemption(
        self, application: CouponApplication, *, user_id: uuid.UUID, order_id: uuid.UUID
    ) -> None:
        self.repo.record_redemption(
            coupon_id=application.coupon.id,
            user_id=user_id,
            order_id=order_id,
            amount_discounted=application.discount_amount,
        )

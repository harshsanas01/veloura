import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from veloura_api.models.coupon import Coupon, CouponRedemption


class CouponRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_code(self, code: str) -> Coupon | None:
        return self.db.scalar(select(Coupon).where(func.upper(Coupon.code) == code.upper()))

    def total_redemptions(self, coupon_id: uuid.UUID) -> int:
        return (
            self.db.scalar(
                select(func.count())
                .select_from(CouponRedemption)
                .where(CouponRedemption.coupon_id == coupon_id)
            )
            or 0
        )

    def user_redemptions(self, coupon_id: uuid.UUID, user_id: uuid.UUID) -> int:
        return (
            self.db.scalar(
                select(func.count())
                .select_from(CouponRedemption)
                .where(CouponRedemption.coupon_id == coupon_id, CouponRedemption.user_id == user_id)
            )
            or 0
        )

    def record_redemption(
        self, *, coupon_id: uuid.UUID, user_id: uuid.UUID, order_id: uuid.UUID, amount_discounted: float
    ) -> None:
        self.db.add(
            CouponRedemption(
                coupon_id=coupon_id,
                user_id=user_id,
                order_id=order_id,
                amount_discounted=amount_discounted,
            )
        )

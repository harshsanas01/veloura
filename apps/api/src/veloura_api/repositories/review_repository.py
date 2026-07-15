import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from veloura_api.models.order import Order, OrderItem, OrderStatus
from veloura_api.models.product import ProductVariant
from veloura_api.models.review import Review, ReviewHelpfulness


class ReviewRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, review_id: uuid.UUID) -> Review | None:
        return self.db.scalar(
            select(Review).where(Review.id == review_id).options(joinedload(Review.user))
        )

    def get_by_product_and_user(self, product_id: uuid.UUID, user_id: uuid.UUID) -> Review | None:
        return self.db.scalar(
            select(Review).where(Review.product_id == product_id, Review.user_id == user_id)
        )

    def list_for_product(
        self, product_id: uuid.UUID, *, sort: str, active_only: bool = True
    ) -> list[Review]:
        query = select(Review).where(Review.product_id == product_id).options(joinedload(Review.user))
        if active_only:
            query = query.where(Review.is_active.is_(True))

        if sort == "highest":
            query = query.order_by(Review.rating.desc(), Review.created_at.desc())
        elif sort == "lowest":
            query = query.order_by(Review.rating.asc(), Review.created_at.desc())
        elif sort == "most_helpful":
            helpful_subq = (
                select(ReviewHelpfulness.review_id, func.count().label("cnt"))
                .group_by(ReviewHelpfulness.review_id)
                .subquery()
            )
            query = query.outerjoin(helpful_subq, helpful_subq.c.review_id == Review.id).order_by(
                func.coalesce(helpful_subq.c.cnt, 0).desc(), Review.created_at.desc()
            )
        else:
            query = query.order_by(Review.created_at.desc())

        return list(self.db.scalars(query).unique().all())

    def helpful_count(self, review_id: uuid.UUID) -> int:
        return (
            self.db.scalar(
                select(func.count())
                .select_from(ReviewHelpfulness)
                .where(ReviewHelpfulness.review_id == review_id)
            )
            or 0
        )

    def user_marked_helpful(self, review_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        return (
            self.db.scalar(
                select(ReviewHelpfulness).where(
                    ReviewHelpfulness.review_id == review_id, ReviewHelpfulness.user_id == user_id
                )
            )
            is not None
        )

    def has_purchased(self, product_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        return (
            self.db.scalar(
                select(OrderItem)
                .join(Order, Order.id == OrderItem.order_id)
                .join(ProductVariant, ProductVariant.id == OrderItem.variant_id)
                .where(
                    Order.user_id == user_id,
                    Order.status != OrderStatus.CANCELLED,
                    ProductVariant.product_id == product_id,
                )
                .limit(1)
            )
            is not None
        )

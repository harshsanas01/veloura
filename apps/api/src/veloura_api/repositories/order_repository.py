import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from veloura_api.models.order import Order, OrderItem
from veloura_api.models.product import ProductVariant


class OrderRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_user(self, user_id: uuid.UUID) -> list[Order]:
        return list(
            self.db.scalars(
                select(Order)
                .where(Order.user_id == user_id)
                .options(selectinload(Order.items))
                .order_by(Order.created_at.desc())
            ).all()
        )

    def get_by_id(self, order_id: uuid.UUID) -> Order | None:
        return self.db.scalar(
            select(Order)
            .where(Order.id == order_id)
            .options(
                selectinload(Order.items).joinedload(OrderItem.variant).joinedload(ProductVariant.product),
                selectinload(Order.status_history),
            )
        )

    def list_all(self) -> list[Order]:
        return list(
            self.db.scalars(
                select(Order).options(selectinload(Order.items)).order_by(Order.created_at.desc())
            ).all()
        )

    def lock_variant(self, variant_id: uuid.UUID) -> ProductVariant | None:
        return self.db.scalar(
            select(ProductVariant)
            .where(ProductVariant.id == variant_id)
            .options(selectinload(ProductVariant.product))
            .with_for_update()
        )

    def next_order_number(self) -> str:
        from sqlalchemy import func

        total = self.db.scalar(select(func.count()).select_from(Order)) or 0
        return f"VLR{100000 + total + 1}"

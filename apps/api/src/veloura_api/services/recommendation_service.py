import datetime
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from veloura_api.ai.outfit_generation import CATEGORY_SLOTS
from veloura_api.models.category import Category
from veloura_api.models.order import Order, OrderItem, OrderStatus
from veloura_api.models.product import Gender, Product, ProductVariant
from veloura_api.repositories.product_repository import ProductRepository
from veloura_api.schemas.product import ProductListItemOut
from veloura_api.services.product_service import _to_list_item

TRENDING_WINDOW_DAYS = 30


class RecommendationService:
    """Deterministic, SQL-driven recommendation sections. Intentionally not a
    machine-learning system - see project docs for rationale."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.products = ProductRepository(db)

    def trending(self, *, gender: Gender | None, limit: int = 8) -> list[ProductListItemOut]:
        since = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=TRENDING_WINDOW_DAYS)

        sales_subq = (
            select(ProductVariant.product_id, func.sum(OrderItem.quantity).label("units_sold"))
            .join(OrderItem, OrderItem.variant_id == ProductVariant.id)
            .join(Order, Order.id == OrderItem.order_id)
            .where(Order.status != OrderStatus.CANCELLED, Order.created_at >= since)
            .group_by(ProductVariant.product_id)
            .subquery()
        )

        query = (
            select(Product)
            .join(sales_subq, sales_subq.c.product_id == Product.id)
            .where(Product.is_active.is_(True))
            .options(selectinload(Product.variants), joinedload(Product.category))
            .order_by(sales_subq.c.units_sold.desc())
        )
        if gender:
            query = query.where(Product.gender.in_([gender, Gender.UNISEX]))

        products = list(self.db.scalars(query.limit(limit)).unique().all())

        if len(products) < limit:
            # Not enough real sales data yet (e.g. a fresh dev database) -
            # fall back to featured/newest so the section is never empty.
            existing_ids = {p.id for p in products}
            fallback_query = (
                select(Product)
                .where(Product.is_active.is_(True), Product.id.not_in(existing_ids or [uuid.uuid4()]))
                .options(selectinload(Product.variants), joinedload(Product.category))
                .order_by(Product.is_featured.desc(), Product.created_at.desc())
            )
            if gender:
                fallback_query = fallback_query.where(Product.gender.in_([gender, Gender.UNISEX]))
            for p in self.db.scalars(fallback_query.limit(limit - len(products))).unique().all():
                products.append(p)

        return [_to_list_item(p) for p in products]

    def also_bought(self, product_id: uuid.UUID, *, limit: int = 4) -> list[ProductListItemOut]:
        co_purchased_orders = (
            select(OrderItem.order_id)
            .join(ProductVariant, ProductVariant.id == OrderItem.variant_id)
            .where(ProductVariant.product_id == product_id)
        )

        # Aggregate co-occurrence counts on IDs only (no eager-loaded columns),
        # then fetch the full ordered Product rows in a second, clean query -
        # mixing GROUP BY with joinedload's extra selected columns breaks SQL.
        ranked_ids = (
            select(Product.id, func.count().label("co_occurrences"))
            .join(ProductVariant, ProductVariant.product_id == Product.id)
            .join(OrderItem, OrderItem.variant_id == ProductVariant.id)
            .where(
                OrderItem.order_id.in_(co_purchased_orders),
                Product.id != product_id,
                Product.is_active.is_(True),
            )
            .group_by(Product.id)
            .order_by(func.count().desc())
            .limit(limit)
        )
        ordered_ids = [row[0] for row in self.db.execute(ranked_ids).all()]

        products_by_id = {
            p.id: p
            for p in self.db.scalars(
                select(Product)
                .where(Product.id.in_(ordered_ids))
                .options(selectinload(Product.variants), joinedload(Product.category))
            ).unique()
        }
        products = [products_by_id[pid] for pid in ordered_ids if pid in products_by_id]

        if len(products) < limit:
            product = self.products.get_by_id(product_id)
            if product:
                existing_ids = {p.id for p in products} | {product_id}
                related = self.products.get_related(product, limit=limit - len(products))
                for p in related:
                    if p.id not in existing_ids:
                        products.append(p)

        return [_to_list_item(p) for p in products]

    def complete_the_look(self, product_id: uuid.UUID, *, limit: int = 4) -> list[ProductListItemOut]:
        product = self.products.get_by_id(product_id)
        if not product:
            return []

        own_slot = CATEGORY_SLOTS.get(product.category.slug)
        compatible_genders = (
            [Gender.MEN, Gender.UNISEX]
            if product.gender == Gender.MEN
            else [Gender.WOMEN, Gender.UNISEX]
            if product.gender == Gender.WOMEN
            else [Gender.MEN, Gender.WOMEN, Gender.UNISEX]
        )

        results: list[Product] = []
        seen_slots = {own_slot} if own_slot else set()
        for slug, slot in CATEGORY_SLOTS.items():
            if slot in seen_slots or slug == product.category.slug:
                continue
            seen_slots.add(slot)
            candidate = self.db.scalar(
                select(Product)
                .join(Category, Category.id == Product.category_id)
                .where(
                    Category.slug == slug,
                    Product.gender.in_(compatible_genders),
                    Product.is_active.is_(True),
                    Product.id != product_id,
                )
                .options(selectinload(Product.variants), joinedload(Product.category))
                .order_by(Product.is_featured.desc(), func.random())
                .limit(1)
            )
            if candidate:
                results.append(candidate)
            if len(results) >= limit:
                break

        return [_to_list_item(p) for p in results]

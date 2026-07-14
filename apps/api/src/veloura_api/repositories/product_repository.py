import uuid

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from veloura_api.models.category import Category
from veloura_api.models.product import Gender, Product, ProductVariant
from veloura_api.schemas.product import ProductFilterParams, SortOption


class ProductRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _base_query(self, filters: ProductFilterParams, *, active_only: bool = True):
        query = select(Product).join(Category, Product.category_id == Category.id)
        if active_only:
            query = query.where(Product.is_active.is_(True))
        if filters.gender:
            query = query.where(Product.gender == filters.gender)
        if filters.category:
            query = query.where(Category.slug.in_(filters.category))
        if filters.q:
            like = f"%{filters.q.lower()}%"
            query = query.where(
                func.lower(Product.name).like(like)
                | func.lower(Product.brand).like(like)
                | func.lower(Product.description).like(like)
            )
        if filters.min_price is not None:
            query = query.where(
                func.coalesce(Product.sale_price, Product.base_price) >= filters.min_price
            )
        if filters.max_price is not None:
            query = query.where(
                func.coalesce(Product.sale_price, Product.base_price) <= filters.max_price
            )
        if filters.size or filters.color:
            variant_conditions = []
            if filters.size:
                variant_conditions.append(ProductVariant.size.in_(filters.size))
            if filters.color:
                variant_conditions.append(ProductVariant.color_name.in_(filters.color))
            query = query.where(
                Product.id.in_(
                    select(ProductVariant.product_id).where(and_(*variant_conditions))
                )
            )
        return query

    def list_products(
        self, filters: ProductFilterParams, *, active_only: bool = True
    ) -> tuple[list[Product], int]:
        base_query = self._base_query(filters, active_only=active_only)

        total = self.db.scalar(select(func.count()).select_from(base_query.subquery())) or 0

        query = base_query.options(
            selectinload(Product.variants), joinedload(Product.category)
        )

        if filters.sort == SortOption.PRICE_ASC:
            query = query.order_by(func.coalesce(Product.sale_price, Product.base_price).asc())
        elif filters.sort == SortOption.PRICE_DESC:
            query = query.order_by(func.coalesce(Product.sale_price, Product.base_price).desc())
        elif filters.sort == SortOption.FEATURED:
            query = query.order_by(Product.is_featured.desc(), Product.created_at.desc())
        elif filters.sort == SortOption.NAME_ASC:
            query = query.order_by(Product.name.asc())
        else:
            query = query.order_by(Product.created_at.desc())

        offset = (filters.page - 1) * filters.page_size
        query = query.offset(offset).limit(filters.page_size)

        items = list(self.db.scalars(query).unique().all())
        return items, total

    def get_by_slug(self, slug: str, *, active_only: bool = True) -> Product | None:
        query = (
            select(Product)
            .where(Product.slug == slug)
            .options(selectinload(Product.variants), joinedload(Product.category))
        )
        if active_only:
            query = query.where(Product.is_active.is_(True))
        return self.db.scalar(query)

    def get_by_id(self, product_id: uuid.UUID) -> Product | None:
        return self.db.scalar(
            select(Product)
            .where(Product.id == product_id)
            .options(selectinload(Product.variants), joinedload(Product.category))
        )

    def get_related(self, product: Product, limit: int = 4) -> list[Product]:
        query = (
            select(Product)
            .where(
                Product.id != product.id,
                Product.is_active.is_(True),
                Product.category_id == product.category_id,
            )
            .options(selectinload(Product.variants), joinedload(Product.category))
            .order_by(func.random())
            .limit(limit)
        )
        results = list(self.db.scalars(query).unique().all())
        if len(results) < limit:
            fallback_query = (
                select(Product)
                .where(
                    Product.id != product.id,
                    Product.is_active.is_(True),
                    Product.gender.in_([product.gender, Gender.UNISEX]),
                )
                .options(selectinload(Product.variants), joinedload(Product.category))
                .order_by(func.random())
                .limit(limit - len(results))
            )
            existing_ids = {p.id for p in results}
            for p in self.db.scalars(fallback_query).unique().all():
                if p.id not in existing_ids:
                    results.append(p)
        return results

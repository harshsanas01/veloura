import uuid

from sqlalchemy import ColumnElement, and_, func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from veloura_api.models.category import Category
from veloura_api.models.product import Gender, Product, ProductVariant
from veloura_api.schemas.product import ProductFacetsOut, ProductFilterParams, SortOption


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
        if filters.brand:
            query = query.where(Product.brand.in_(filters.brand))
        if filters.material:
            query = query.where(Product.material.in_(filters.material))
        if filters.occasion:
            query = query.where(Product.occasion_tags.op("&&")(filters.occasion))
        if filters.season:
            query = query.where(Product.season_tags.op("&&")(filters.season))
        if filters.sale_only:
            query = query.where(Product.sale_price.is_not(None))
        if filters.q:
            like = f"%{filters.q.lower()}%"
            tags_text = func.array_to_string(
                Product.occasion_tags + Product.style_tags + Product.season_tags, ","
            )
            query = query.where(
                func.lower(Product.name).like(like)
                | func.lower(Product.brand).like(like)
                | func.lower(Product.description).like(like)
                | func.lower(Product.material).like(like)
                | func.lower(tags_text).like(like)
                | Product.id.in_(
                    select(ProductVariant.product_id).where(func.lower(ProductVariant.color_name).like(like))
                )
            )
        if filters.min_price is not None:
            query = query.where(func.coalesce(Product.sale_price, Product.base_price) >= filters.min_price)
        if filters.max_price is not None:
            query = query.where(func.coalesce(Product.sale_price, Product.base_price) <= filters.max_price)
        if filters.size or filters.color or filters.in_stock_only:
            variant_conditions: list[ColumnElement[bool]] = []
            if filters.size:
                variant_conditions.append(ProductVariant.size.in_(filters.size))
            if filters.color:
                variant_conditions.append(ProductVariant.color_name.in_(filters.color))
            if filters.in_stock_only:
                variant_conditions.append(ProductVariant.inventory_quantity > 0)
            query = query.where(
                Product.id.in_(select(ProductVariant.product_id).where(and_(*variant_conditions)))
            )
        return query

    def list_products(
        self, filters: ProductFilterParams, *, active_only: bool = True
    ) -> tuple[list[Product], int]:
        base_query = self._base_query(filters, active_only=active_only)

        total = self.db.scalar(select(func.count()).select_from(base_query.subquery())) or 0

        query = base_query.options(selectinload(Product.variants), joinedload(Product.category))

        # Product.id is the final tiebreaker on every sort: seeded rows share a
        # created_at (and prices/names repeat), and without a total order the
        # same product can appear on two pages while another is skipped.
        if filters.sort == SortOption.PRICE_ASC:
            query = query.order_by(func.coalesce(Product.sale_price, Product.base_price).asc(), Product.id)
        elif filters.sort == SortOption.PRICE_DESC:
            query = query.order_by(func.coalesce(Product.sale_price, Product.base_price).desc(), Product.id)
        elif filters.sort == SortOption.FEATURED:
            query = query.order_by(Product.is_featured.desc(), Product.created_at.desc(), Product.id)
        elif filters.sort == SortOption.NAME_ASC:
            query = query.order_by(Product.name.asc(), Product.id)
        elif filters.sort == SortOption.BIGGEST_DISCOUNT:
            discount = Product.base_price - func.coalesce(Product.sale_price, Product.base_price)
            query = query.order_by(discount.desc(), Product.created_at.desc(), Product.id)
        else:
            query = query.order_by(Product.created_at.desc(), Product.id)

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
        compatible_genders = (
            [Gender.MEN, Gender.UNISEX]
            if product.gender == Gender.MEN
            else [Gender.WOMEN, Gender.UNISEX]
            if product.gender == Gender.WOMEN
            else [Gender.MEN, Gender.WOMEN, Gender.UNISEX]
        )

        def _query(*, same_category: bool, same_gender: bool):
            conditions = [Product.id != product.id, Product.is_active.is_(True)]
            if same_category:
                conditions.append(Product.category_id == product.category_id)
            if same_gender:
                conditions.append(Product.gender.in_(compatible_genders))
            return (
                select(Product)
                .where(*conditions)
                .options(selectinload(Product.variants), joinedload(Product.category))
                .order_by(func.random())
            )

        results: list[Product] = []
        existing_ids: set = set()

        # Priority 1: same category, gender-compatible (the only case that should ever
        # surface a product to a shopper of the opposite gender's collection).
        for tier_same_category, tier_same_gender in (
            (True, True),
            (False, True),
            (True, False),
        ):
            if len(results) >= limit:
                break
            query = _query(same_category=tier_same_category, same_gender=tier_same_gender).limit(
                limit - len(results)
            )
            for p in self.db.scalars(query).unique().all():
                if p.id not in existing_ids:
                    results.append(p)
                    existing_ids.add(p.id)
        return results[:limit]

    def get_facets(self, *, active_only: bool = True) -> ProductFacetsOut:
        query = select(Product)
        if active_only:
            query = query.where(Product.is_active.is_(True))

        brands = sorted(self.db.scalars(query.with_only_columns(Product.brand).distinct()).all())
        materials = sorted(self.db.scalars(query.with_only_columns(Product.material).distinct()).all())
        occasion_rows = self.db.scalars(query.with_only_columns(Product.occasion_tags)).all()
        occasions = sorted({tag for tags in occasion_rows for tag in tags})
        season_rows = self.db.scalars(query.with_only_columns(Product.season_tags)).all()
        seasons = sorted({tag for tags in season_rows for tag in tags})
        price_query = select(
            func.min(func.coalesce(Product.sale_price, Product.base_price)),
            func.max(func.coalesce(Product.sale_price, Product.base_price)),
        )
        if active_only:
            price_query = price_query.where(Product.is_active.is_(True))
        price_row = self.db.execute(price_query).one()

        return ProductFacetsOut(
            brands=brands,
            materials=materials,
            occasions=occasions,
            seasons=seasons,
            min_price=float(price_row[0] or 0),
            max_price=float(price_row[1] or 0),
        )

import math
import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from veloura_api.ai.client import get_embedding
from veloura_api.models.category import Category
from veloura_api.models.coupon import Coupon, CouponRedemption
from veloura_api.models.inventory_transaction import InventoryChangeReason, InventoryTransaction
from veloura_api.models.order import Order, OrderItem, OrderStatus
from veloura_api.models.order_status_history import OrderStatusHistory
from veloura_api.models.product import Product, ProductVariant
from veloura_api.models.user import User
from veloura_api.repositories.order_repository import OrderRepository
from veloura_api.repositories.product_repository import ProductRepository
from veloura_api.schemas.admin import (
    AdminCouponCreate,
    AdminCouponOut,
    AdminCouponUpdate,
    AdminCustomerListResponse,
    AdminCustomerOut,
    AdminDashboardOut,
    AdminOrderItemOut,
    AdminOrderListResponse,
    AdminOrderOut,
    AdminProductCreate,
    AdminProductListResponse,
    AdminProductOut,
    AdminProductUpdate,
    AdminVariantOut,
    AdminVariantUpdate,
    BestSellingProductOut,
    InventoryAdjustmentRequest,
    TopCategoryOut,
)
from veloura_api.utils import embedding_text, slugify

LOW_STOCK_THRESHOLD = 5


def _to_product_out(product: Product) -> AdminProductOut:
    return AdminProductOut(
        id=product.id,
        slug=product.slug,
        name=product.name,
        brand=product.brand,
        gender=product.gender,
        category_id=product.category_id,
        base_price=float(product.base_price),
        sale_price=float(product.sale_price) if product.sale_price else None,
        is_featured=product.is_featured,
        is_active=product.is_active,
        variants=[AdminVariantOut.model_validate(v, from_attributes=True) for v in product.variants],
        created_at=product.created_at,
    )


def _refresh_embedding(product: Product, category_slug: str) -> None:
    colors = list({v.color_name for v in product.variants})
    text = embedding_text(
        name=product.name,
        description=product.description,
        category=category_slug,
        gender=product.gender.value,
        style_tags=product.style_tags,
        occasion_tags=product.occasion_tags,
        season_tags=product.season_tags,
        colors=colors,
    )
    embedding = get_embedding(text)
    if embedding is not None:
        product.embedding = embedding


class AdminService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.products = ProductRepository(db)
        self.orders = OrderRepository(db)

    def list_products(
        self, *, q: str | None = None, page: int = 1, page_size: int = 20
    ) -> AdminProductListResponse:
        query = select(Product)
        if q:
            like = f"%{q.lower()}%"
            query = query.where(func.lower(Product.name).like(like) | func.lower(Product.brand).like(like))

        total = self.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        query = (
            query.options(selectinload(Product.variants))
            .order_by(Product.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        products = list(self.db.scalars(query).unique().all())
        return AdminProductListResponse(
            items=[_to_product_out(p) for p in products],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if total else 0,
        )

    def create_product(self, payload: AdminProductCreate) -> AdminProductOut:
        from veloura_api.models.category import Category

        category = self.db.get(Category, payload.category_id)
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")

        base_slug = slugify(payload.name)
        slug = base_slug
        suffix = 1
        while self.db.scalar(select(Product).where(Product.slug == slug)):
            suffix += 1
            slug = f"{base_slug}-{suffix}"

        product = Product(
            slug=slug,
            name=payload.name,
            brand=payload.brand,
            description=payload.description,
            short_description=payload.short_description,
            gender=payload.gender,
            category_id=payload.category_id,
            base_price=payload.base_price,
            sale_price=payload.sale_price,
            material=payload.material,
            care_instructions=payload.care_instructions,
            occasion_tags=payload.occasion_tags,
            style_tags=payload.style_tags,
            season_tags=payload.season_tags,
            is_featured=payload.is_featured,
            is_active=payload.is_active,
        )
        for v in payload.variants:
            product.variants.append(
                ProductVariant(
                    sku=v.sku,
                    size=v.size,
                    color_name=v.color_name,
                    color_hex=v.color_hex,
                    inventory_quantity=v.inventory_quantity,
                    image_url=v.image_url,
                )
            )
        self.db.add(product)
        self.db.flush()
        _refresh_embedding(product, category.slug)
        self.db.commit()
        self.db.refresh(product)
        return _to_product_out(product)

    def update_product(self, product_id: uuid.UUID, payload: AdminProductUpdate) -> AdminProductOut:
        product = self.products.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)

        from veloura_api.models.category import Category

        category = self.db.get(Category, product.category_id)
        if update_data:
            _refresh_embedding(product, category.slug if category else "")
        self.db.commit()
        self.db.refresh(product)
        return _to_product_out(product)

    def delete_product(self, product_id: uuid.UUID) -> None:
        product = self.products.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
        self.db.delete(product)
        self.db.commit()

    def add_variant(self, product_id: uuid.UUID, payload) -> AdminProductOut:
        product = self.products.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
        product.variants.append(
            ProductVariant(
                sku=payload.sku,
                size=payload.size,
                color_name=payload.color_name,
                color_hex=payload.color_hex,
                inventory_quantity=payload.inventory_quantity,
                image_url=payload.image_url,
            )
        )
        self.db.commit()
        self.db.refresh(product)
        return _to_product_out(product)

    def update_variant(self, variant_id: uuid.UUID, payload: AdminVariantUpdate) -> AdminVariantOut:
        variant = self.db.get(ProductVariant, variant_id)
        if not variant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found.")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(variant, field, value)
        self.db.commit()
        self.db.refresh(variant)
        return AdminVariantOut.model_validate(variant, from_attributes=True)

    def list_orders(
        self,
        *,
        q: str | None = None,
        order_status: OrderStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> AdminOrderListResponse:
        query = select(Order).join(User, Order.user_id == User.id)
        if order_status:
            query = query.where(Order.status == order_status)
        if q:
            like = f"%{q.lower()}%"
            query = query.where(func.lower(Order.order_number).like(like) | func.lower(User.email).like(like))

        total = self.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        query = (
            query.options(selectinload(Order.items))
            .order_by(Order.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        orders = list(self.db.scalars(query).unique().all())
        return AdminOrderListResponse(
            items=[self._to_order_out(o) for o in orders],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if total else 0,
        )

    def _to_order_out(self, order: Order) -> AdminOrderOut:
        user = self.db.get(User, order.user_id)
        return AdminOrderOut(
            id=order.id,
            order_number=order.order_number,
            status=order.status,
            customer_email=user.email if user else "unknown",
            total=float(order.total),
            items=[
                AdminOrderItemOut(
                    product_name=i.product_name,
                    variant_size=i.variant_size,
                    variant_color=i.variant_color,
                    unit_price=float(i.unit_price),
                    quantity=i.quantity,
                )
                for i in order.items
            ],
            created_at=order.created_at,
        )

    def update_order_status(
        self, order_id: uuid.UUID, new_status: OrderStatus, *, note: str | None = None
    ) -> AdminOrderOut:
        order = self.orders.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

        restoring_statuses = {OrderStatus.CANCELLED, OrderStatus.RETURNED}
        if new_status in restoring_statuses and order.status not in restoring_statuses:
            reason = (
                InventoryChangeReason.RETURN
                if new_status == OrderStatus.RETURNED
                else InventoryChangeReason.ORDER_CANCELLED
            )
            for item in order.items:
                variant = self.orders.lock_variant(item.variant_id)
                if variant:
                    variant.inventory_quantity += item.quantity
                    self.db.add(
                        InventoryTransaction(
                            variant_id=variant.id,
                            change_quantity=item.quantity,
                            resulting_quantity=variant.inventory_quantity,
                            reason=reason,
                            order_id=order.id,
                        )
                    )

        order.status = new_status
        self.db.add(OrderStatusHistory(order_id=order.id, status=new_status, note=note))
        self.db.commit()
        return self._to_order_out(order)

    def delete_variant(self, variant_id: uuid.UUID) -> None:
        variant = self.db.get(ProductVariant, variant_id)
        if not variant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found.")
        self.db.delete(variant)
        self.db.commit()

    def adjust_inventory(
        self, variant_id: uuid.UUID, admin_user_id: uuid.UUID, payload: InventoryAdjustmentRequest
    ) -> AdminVariantOut:
        variant = self.db.get(ProductVariant, variant_id)
        if not variant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found.")
        new_quantity = variant.inventory_quantity + payload.delta
        if new_quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot reduce inventory below zero (current: {variant.inventory_quantity}).",
            )
        variant.inventory_quantity = new_quantity
        self.db.add(
            InventoryTransaction(
                variant_id=variant.id,
                change_quantity=payload.delta,
                resulting_quantity=new_quantity,
                reason=InventoryChangeReason.ADMIN_ADJUSTMENT,
                admin_user_id=admin_user_id,
                note=payload.reason,
            )
        )
        self.db.commit()
        self.db.refresh(variant)
        return AdminVariantOut.model_validate(variant, from_attributes=True)

    def list_customers(
        self, *, q: str | None = None, page: int = 1, page_size: int = 20
    ) -> AdminCustomerListResponse:
        query = select(User)
        if q:
            like = f"%{q.lower()}%"
            query = query.where(
                func.lower(User.email).like(like)
                | func.lower(User.first_name).like(like)
                | func.lower(User.last_name).like(like)
            )

        total = self.db.scalar(select(func.count()).select_from(query.subquery())) or 0
        query = query.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        users = list(self.db.scalars(query).all())

        items = []
        for user in users:
            stats = self.db.execute(
                select(func.count(Order.id), func.coalesce(func.sum(Order.total), 0)).where(
                    Order.user_id == user.id, Order.status != OrderStatus.CANCELLED
                )
            ).one()
            items.append(
                AdminCustomerOut(
                    id=user.id,
                    email=user.email,
                    full_name=user.full_name,
                    role=user.role.value,
                    is_active=user.is_active,
                    order_count=stats[0],
                    total_spent=float(stats[1]),
                    created_at=user.created_at,
                )
            )
        return AdminCustomerListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if total else 0,
        )

    def get_dashboard(self) -> AdminDashboardOut:
        total_revenue = (
            self.db.scalar(
                select(func.coalesce(func.sum(Order.total), 0)).where(Order.status != OrderStatus.CANCELLED)
            )
            or 0
        )
        total_orders = self.db.scalar(select(func.count()).select_from(Order)) or 0
        total_customers = self.db.scalar(select(func.count()).select_from(User)) or 0
        average_order_value = float(total_revenue) / total_orders if total_orders else 0.0

        low_stock = (
            self.db.scalar(
                select(func.count()).where(
                    ProductVariant.inventory_quantity > 0,
                    ProductVariant.inventory_quantity <= LOW_STOCK_THRESHOLD,
                )
            )
            or 0
        )
        out_of_stock = self.db.scalar(select(func.count()).where(ProductVariant.inventory_quantity == 0)) or 0

        best_sellers = self.db.execute(
            select(Product.id, Product.name, Product.slug, func.sum(OrderItem.quantity).label("units_sold"))
            .join(ProductVariant, ProductVariant.product_id == Product.id)
            .join(OrderItem, OrderItem.variant_id == ProductVariant.id)
            .join(Order, Order.id == OrderItem.order_id)
            .where(Order.status != OrderStatus.CANCELLED)
            .group_by(Product.id)
            .order_by(func.sum(OrderItem.quantity).desc())
            .limit(5)
        ).all()

        top_categories = self.db.execute(
            select(
                Category.name,
                Category.slug,
                func.coalesce(func.sum(OrderItem.unit_price * OrderItem.quantity), 0),
            )
            .select_from(OrderItem)
            .join(Order, Order.id == OrderItem.order_id)
            .join(ProductVariant, ProductVariant.id == OrderItem.variant_id)
            .join(Product, Product.id == ProductVariant.product_id)
            .join(Category, Category.id == Product.category_id)
            .where(Order.status != OrderStatus.CANCELLED)
            .group_by(Category.id)
            .order_by(func.sum(OrderItem.unit_price * OrderItem.quantity).desc())
            .limit(5)
        ).all()

        recent_orders = list(
            self.db.scalars(
                select(Order).options(selectinload(Order.items)).order_by(Order.created_at.desc()).limit(5)
            ).all()
        )

        return AdminDashboardOut(
            total_revenue=float(total_revenue),
            total_orders=total_orders,
            total_customers=total_customers,
            average_order_value=round(average_order_value, 2),
            low_stock_variant_count=low_stock,
            out_of_stock_variant_count=out_of_stock,
            best_selling_products=[
                BestSellingProductOut(product_id=row[0], name=row[1], slug=row[2], units_sold=int(row[3]))
                for row in best_sellers
            ],
            recent_orders=[self._to_order_out(o) for o in recent_orders],
            top_categories=[
                TopCategoryOut(category_name=row[0], category_slug=row[1], revenue=float(row[2]))
                for row in top_categories
            ],
        )

    def list_coupons(self) -> list[AdminCouponOut]:
        coupons = list(self.db.scalars(select(Coupon).order_by(Coupon.created_at.desc())).all())
        return [self._to_coupon_out(c) for c in coupons]

    def _to_coupon_out(self, coupon: Coupon) -> AdminCouponOut:
        total_redemptions = (
            self.db.scalar(
                select(func.count())
                .select_from(CouponRedemption)
                .where(CouponRedemption.coupon_id == coupon.id)
            )
            or 0
        )
        return AdminCouponOut(
            id=coupon.id,
            code=coupon.code,
            discount_type=coupon.discount_type,
            discount_value=float(coupon.discount_value),
            free_shipping=coupon.free_shipping,
            min_order_value=float(coupon.min_order_value) if coupon.min_order_value is not None else None,
            max_discount=float(coupon.max_discount) if coupon.max_discount is not None else None,
            starts_at=coupon.starts_at,
            expires_at=coupon.expires_at,
            is_active=coupon.is_active,
            usage_limit=coupon.usage_limit,
            per_user_limit=coupon.per_user_limit,
            applicable_categories=coupon.applicable_categories,
            applicable_products=coupon.applicable_products,
            total_redemptions=total_redemptions,
            created_at=coupon.created_at,
        )

    def create_coupon(self, payload: AdminCouponCreate) -> AdminCouponOut:
        if self.db.scalar(select(Coupon).where(func.upper(Coupon.code) == payload.code.upper())):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="A coupon with this code already exists."
            )
        coupon = Coupon(**{**payload.model_dump(), "code": payload.code.upper()})
        self.db.add(coupon)
        self.db.commit()
        self.db.refresh(coupon)
        return self._to_coupon_out(coupon)

    def update_coupon(self, coupon_id: uuid.UUID, payload: AdminCouponUpdate) -> AdminCouponOut:
        coupon = self.db.get(Coupon, coupon_id)
        if not coupon:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coupon not found.")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(coupon, field, value)
        self.db.commit()
        self.db.refresh(coupon)
        return self._to_coupon_out(coupon)

    def delete_coupon(self, coupon_id: uuid.UUID) -> None:
        coupon = self.db.get(Coupon, coupon_id)
        if not coupon:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coupon not found.")
        self.db.delete(coupon)
        self.db.commit()

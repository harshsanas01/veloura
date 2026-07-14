import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from veloura_api.ai.client import get_embedding
from veloura_api.models.order import Order, OrderStatus
from veloura_api.models.product import Product, ProductVariant
from veloura_api.models.user import User
from veloura_api.repositories.order_repository import OrderRepository
from veloura_api.repositories.product_repository import ProductRepository
from veloura_api.schemas.admin import (
    AdminOrderItemOut,
    AdminOrderOut,
    AdminProductCreate,
    AdminProductOut,
    AdminProductUpdate,
    AdminVariantOut,
    AdminVariantUpdate,
)
from veloura_api.utils import embedding_text, slugify


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

    def list_products(self) -> list[AdminProductOut]:
        products = list(
            self.db.scalars(
                select(Product).options(selectinload(Product.variants)).order_by(Product.created_at.desc())
            ).all()
        )
        return [_to_product_out(p) for p in products]

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

    def list_orders(self) -> list[AdminOrderOut]:
        orders = list(
            self.db.scalars(
                select(Order)
                .join(User, Order.user_id == User.id)
                .options(selectinload(Order.items))
                .order_by(Order.created_at.desc())
            ).all()
        )
        result = []
        for o in orders:
            user = self.db.get(User, o.user_id)
            result.append(
                AdminOrderOut(
                    id=o.id,
                    order_number=o.order_number,
                    status=o.status,
                    customer_email=user.email if user else "unknown",
                    total=float(o.total),
                    items=[
                        AdminOrderItemOut(
                            product_name=i.product_name,
                            variant_size=i.variant_size,
                            variant_color=i.variant_color,
                            unit_price=float(i.unit_price),
                            quantity=i.quantity,
                        )
                        for i in o.items
                    ],
                    created_at=o.created_at,
                )
            )
        return result

    def update_order_status(self, order_id: uuid.UUID, new_status: OrderStatus) -> AdminOrderOut:
        order = self.orders.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
        order.status = new_status
        self.db.commit()
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

import math
import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from veloura_api.models.product import Product
from veloura_api.repositories.product_repository import ProductRepository
from veloura_api.schemas.category import CategoryOut
from veloura_api.schemas.product import (
    ProductFilterParams,
    ProductListItemOut,
    ProductListResponse,
    ProductOut,
    ProductVariantOut,
)

PLACEHOLDER_IMAGE = "https://images.unsplash.com/photo-1445205170230-053b83016050?w=800&q=80"


def _to_list_item(product: Product) -> ProductListItemOut:
    primary_image = product.variants[0].image_url if product.variants else PLACEHOLDER_IMAGE
    colors = list({v.color_hex for v in product.variants})
    in_stock = any(v.inventory_quantity > 0 for v in product.variants)
    return ProductListItemOut(
        id=product.id,
        slug=product.slug,
        name=product.name,
        brand=product.brand,
        gender=product.gender,
        category_slug=product.category.slug,
        category_name=product.category.name,
        base_price=float(product.base_price),
        sale_price=float(product.sale_price) if product.sale_price else None,
        effective_price=product.effective_price,
        primary_image=primary_image,
        available_colors=colors,
        is_featured=product.is_featured,
        in_stock=in_stock,
    )


def _to_detail(product: Product) -> ProductOut:
    sizes = sorted({v.size for v in product.variants})
    colors: dict[str, dict] = {}
    for v in product.variants:
        colors.setdefault(v.color_name, {"name": v.color_name, "hex": v.color_hex})
    return ProductOut(
        id=product.id,
        slug=product.slug,
        name=product.name,
        brand=product.brand,
        description=product.description,
        short_description=product.short_description,
        gender=product.gender,
        category=CategoryOut.model_validate(product.category),
        base_price=float(product.base_price),
        sale_price=float(product.sale_price) if product.sale_price else None,
        effective_price=product.effective_price,
        material=product.material,
        care_instructions=product.care_instructions,
        occasion_tags=product.occasion_tags,
        style_tags=product.style_tags,
        season_tags=product.season_tags,
        is_featured=product.is_featured,
        variants=[ProductVariantOut.model_validate(v) for v in product.variants],
        available_sizes=sizes,
        available_colors=list(colors.values()),
    )


class ProductService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ProductRepository(db)

    def list_products(self, filters: ProductFilterParams) -> ProductListResponse:
        products, total = self.repo.list_products(filters)
        total_pages = math.ceil(total / filters.page_size) if total else 0
        return ProductListResponse(
            items=[_to_list_item(p) for p in products],
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            total_pages=total_pages,
        )

    def get_by_slug(self, slug: str) -> ProductOut:
        product = self.repo.get_by_slug(slug)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
        return _to_detail(product)

    def get_related(self, product_id: uuid.UUID, limit: int = 4) -> list[ProductListItemOut]:
        product = self.repo.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
        related = self.repo.get_related(product, limit=limit)
        return [_to_list_item(p) for p in related]

import uuid
from typing import Annotated

from fastapi import APIRouter, Query

from veloura_api.dependencies import DbSession
from veloura_api.models.product import Gender
from veloura_api.schemas.product import (
    ProductFacetsOut,
    ProductFilterParams,
    ProductListItemOut,
    ProductListResponse,
    ProductOut,
    SortOption,
)
from veloura_api.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=ProductListResponse)
def list_products(
    db: DbSession,
    q: str | None = None,
    gender: Gender | None = None,
    category: Annotated[list[str] | None, Query()] = None,
    size: Annotated[list[str] | None, Query()] = None,
    color: Annotated[list[str] | None, Query()] = None,
    brand: Annotated[list[str] | None, Query()] = None,
    material: Annotated[list[str] | None, Query()] = None,
    occasion: Annotated[list[str] | None, Query()] = None,
    season: Annotated[list[str] | None, Query()] = None,
    min_price: float | None = None,
    max_price: float | None = None,
    in_stock_only: bool = False,
    sale_only: bool = False,
    sort: SortOption = SortOption.NEWEST,
    page: int = 1,
    page_size: int = 12,
) -> ProductListResponse:
    filters = ProductFilterParams(
        q=q,
        gender=gender,
        category=category,
        size=size,
        color=color,
        brand=brand,
        material=material,
        occasion=occasion,
        season=season,
        min_price=min_price,
        max_price=max_price,
        in_stock_only=in_stock_only,
        sale_only=sale_only,
        sort=sort,
        page=page,
        page_size=page_size,
    )
    return ProductService(db).list_products(filters)


@router.get("/facets", response_model=ProductFacetsOut)
def get_facets(db: DbSession) -> ProductFacetsOut:
    return ProductService(db).get_facets()


@router.get("/{slug}", response_model=ProductOut)
def get_product(slug: str, db: DbSession) -> ProductOut:
    return ProductService(db).get_by_slug(slug)


@router.get("/{product_id}/related", response_model=list[ProductListItemOut])
def get_related_products(product_id: uuid.UUID, db: DbSession) -> list[ProductListItemOut]:
    return ProductService(db).get_related(product_id)

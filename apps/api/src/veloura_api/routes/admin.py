import uuid

from fastapi import APIRouter

from veloura_api.dependencies import CurrentAdmin, DbSession
from veloura_api.schemas.admin import (
    AdminOrderOut,
    AdminProductCreate,
    AdminProductOut,
    AdminProductUpdate,
    AdminVariantInput,
    AdminVariantOut,
    AdminVariantUpdate,
)
from veloura_api.schemas.order import UpdateOrderStatusRequest
from veloura_api.services.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/products", response_model=list[AdminProductOut])
def list_products(current_admin: CurrentAdmin, db: DbSession) -> list[AdminProductOut]:
    return AdminService(db).list_products()


@router.post("/products", response_model=AdminProductOut, status_code=201)
def create_product(
    payload: AdminProductCreate, current_admin: CurrentAdmin, db: DbSession
) -> AdminProductOut:
    return AdminService(db).create_product(payload)


@router.patch("/products/{product_id}", response_model=AdminProductOut)
def update_product(
    product_id: uuid.UUID, payload: AdminProductUpdate, current_admin: CurrentAdmin, db: DbSession
) -> AdminProductOut:
    return AdminService(db).update_product(product_id, payload)


@router.delete("/products/{product_id}", status_code=204)
def delete_product(product_id: uuid.UUID, current_admin: CurrentAdmin, db: DbSession) -> None:
    AdminService(db).delete_product(product_id)


@router.post("/products/{product_id}/variants", response_model=AdminProductOut, status_code=201)
def add_variant(
    product_id: uuid.UUID, payload: AdminVariantInput, current_admin: CurrentAdmin, db: DbSession
) -> AdminProductOut:
    return AdminService(db).add_variant(product_id, payload)


@router.patch("/variants/{variant_id}", response_model=AdminVariantOut)
def update_variant(
    variant_id: uuid.UUID, payload: AdminVariantUpdate, current_admin: CurrentAdmin, db: DbSession
) -> AdminVariantOut:
    return AdminService(db).update_variant(variant_id, payload)


@router.get("/orders", response_model=list[AdminOrderOut])
def list_orders(current_admin: CurrentAdmin, db: DbSession) -> list[AdminOrderOut]:
    return AdminService(db).list_orders()


@router.patch("/orders/{order_id}/status", response_model=AdminOrderOut)
def update_order_status(
    order_id: uuid.UUID,
    payload: UpdateOrderStatusRequest,
    current_admin: CurrentAdmin,
    db: DbSession,
) -> AdminOrderOut:
    return AdminService(db).update_order_status(order_id, payload.status)

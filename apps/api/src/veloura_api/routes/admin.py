import uuid

from fastapi import APIRouter

from veloura_api.dependencies import CurrentAdmin, DbSession
from veloura_api.models.order import OrderStatus
from veloura_api.schemas.admin import (
    AdminCouponCreate,
    AdminCouponOut,
    AdminCouponUpdate,
    AdminCustomerListResponse,
    AdminDashboardOut,
    AdminOrderListResponse,
    AdminOrderOut,
    AdminProductCreate,
    AdminProductListResponse,
    AdminProductOut,
    AdminProductUpdate,
    AdminVariantInput,
    AdminVariantOut,
    AdminVariantUpdate,
    InventoryAdjustmentRequest,
)
from veloura_api.schemas.order import UpdateOrderStatusRequest
from veloura_api.schemas.review import AdminReviewModerateRequest, ReviewOut
from veloura_api.services.admin_service import AdminService
from veloura_api.services.review_service import ReviewService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard", response_model=AdminDashboardOut)
def get_dashboard(current_admin: CurrentAdmin, db: DbSession) -> AdminDashboardOut:
    return AdminService(db).get_dashboard()


@router.get("/reviews", response_model=list[ReviewOut])
def list_all_reviews(current_admin: CurrentAdmin, db: DbSession) -> list[ReviewOut]:
    return ReviewService(db).list_all_for_admin()


@router.patch("/reviews/{review_id}", response_model=ReviewOut)
def moderate_review(
    review_id: uuid.UUID,
    payload: AdminReviewModerateRequest,
    current_admin: CurrentAdmin,
    db: DbSession,
) -> ReviewOut:
    return ReviewService(db).moderate(review_id, payload.is_active)


@router.get("/products", response_model=AdminProductListResponse)
def list_products(
    current_admin: CurrentAdmin,
    db: DbSession,
    q: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> AdminProductListResponse:
    return AdminService(db).list_products(q=q, page=page, page_size=page_size)


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


@router.delete("/variants/{variant_id}", status_code=204)
def delete_variant(variant_id: uuid.UUID, current_admin: CurrentAdmin, db: DbSession) -> None:
    AdminService(db).delete_variant(variant_id)


@router.post("/variants/{variant_id}/adjust-inventory", response_model=AdminVariantOut)
def adjust_inventory(
    variant_id: uuid.UUID,
    payload: InventoryAdjustmentRequest,
    current_admin: CurrentAdmin,
    db: DbSession,
) -> AdminVariantOut:
    return AdminService(db).adjust_inventory(variant_id, current_admin.id, payload)


@router.get("/orders", response_model=AdminOrderListResponse)
def list_orders(
    current_admin: CurrentAdmin,
    db: DbSession,
    q: str | None = None,
    order_status: OrderStatus | None = None,
    page: int = 1,
    page_size: int = 20,
) -> AdminOrderListResponse:
    return AdminService(db).list_orders(q=q, order_status=order_status, page=page, page_size=page_size)


@router.patch("/orders/{order_id}/status", response_model=AdminOrderOut)
def update_order_status(
    order_id: uuid.UUID,
    payload: UpdateOrderStatusRequest,
    current_admin: CurrentAdmin,
    db: DbSession,
) -> AdminOrderOut:
    return AdminService(db).update_order_status(order_id, payload.status, note=payload.note)


@router.get("/customers", response_model=AdminCustomerListResponse)
def list_customers(
    current_admin: CurrentAdmin,
    db: DbSession,
    q: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> AdminCustomerListResponse:
    return AdminService(db).list_customers(q=q, page=page, page_size=page_size)


@router.get("/coupons", response_model=list[AdminCouponOut])
def list_coupons(current_admin: CurrentAdmin, db: DbSession) -> list[AdminCouponOut]:
    return AdminService(db).list_coupons()


@router.post("/coupons", response_model=AdminCouponOut, status_code=201)
def create_coupon(
    payload: AdminCouponCreate, current_admin: CurrentAdmin, db: DbSession
) -> AdminCouponOut:
    return AdminService(db).create_coupon(payload)


@router.patch("/coupons/{coupon_id}", response_model=AdminCouponOut)
def update_coupon(
    coupon_id: uuid.UUID, payload: AdminCouponUpdate, current_admin: CurrentAdmin, db: DbSession
) -> AdminCouponOut:
    return AdminService(db).update_coupon(coupon_id, payload)


@router.delete("/coupons/{coupon_id}", status_code=204)
def delete_coupon(coupon_id: uuid.UUID, current_admin: CurrentAdmin, db: DbSession) -> None:
    AdminService(db).delete_coupon(coupon_id)

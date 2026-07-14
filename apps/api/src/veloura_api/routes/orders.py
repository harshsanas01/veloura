import uuid

from fastapi import APIRouter

from veloura_api.dependencies import CurrentUser, DbSession
from veloura_api.schemas.order import CreateOrderRequest, OrderOut, OrderSummaryOut
from veloura_api.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderOut, status_code=201)
def create_order(payload: CreateOrderRequest, current_user: CurrentUser, db: DbSession) -> OrderOut:
    return OrderService(db).create_order(current_user.id, payload)


@router.get("", response_model=list[OrderSummaryOut])
def list_orders(current_user: CurrentUser, db: DbSession) -> list[OrderSummaryOut]:
    return OrderService(db).list_orders(current_user.id)


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> OrderOut:
    return OrderService(db).get_order(current_user.id, order_id)

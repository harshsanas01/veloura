import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from veloura_api.models.inventory_transaction import InventoryChangeReason, InventoryTransaction
from veloura_api.models.order import CUSTOMER_CANCELLABLE_STATUSES, Order, OrderItem, OrderStatus
from veloura_api.models.order_status_history import OrderStatusHistory
from veloura_api.repositories.cart_repository import CartRepository
from veloura_api.repositories.order_repository import OrderRepository
from veloura_api.schemas.order import (
    CreateOrderRequest,
    OrderItemOut,
    OrderOut,
    OrderStatusHistoryOut,
    OrderSummaryOut,
)
from veloura_api.services.coupon_service import CouponError, CouponService
from veloura_api.services.pricing import calculate_order_totals


def _to_order_out(order: Order) -> OrderOut:
    items = []
    for item in order.items:
        image_url = None
        slug = None
        if item.variant is not None:
            image_url = item.variant.image_url
            slug = item.variant.product.slug if item.variant.product else None
        items.append(
            OrderItemOut(
                id=item.id,
                product_name=item.product_name,
                variant_size=item.variant_size,
                variant_color=item.variant_color,
                unit_price=float(item.unit_price),
                quantity=item.quantity,
                line_total=round(float(item.unit_price) * item.quantity, 2),
                product_slug=slug,
                image_url=image_url,
            )
        )
    return OrderOut(
        id=order.id,
        order_number=order.order_number,
        status=order.status,
        subtotal=float(order.subtotal),
        discount_amount=float(order.discount_amount),
        shipping_cost=float(order.shipping_cost),
        tax=float(order.tax),
        total=float(order.total),
        coupon_code=order.coupon_code,
        customer_notes=order.customer_notes,
        shipping_address=order.shipping_address,
        items=items,
        status_history=[
            OrderStatusHistoryOut(status=h.status, note=h.note, created_at=h.created_at)
            for h in order.status_history
        ],
        can_cancel=order.status in CUSTOMER_CANCELLABLE_STATUSES,
        created_at=order.created_at,
    )


class OrderService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = OrderRepository(db)
        self.cart_repo = CartRepository(db)
        self.coupons = CouponService(db)

    def create_order(self, user_id: uuid.UUID, payload: CreateOrderRequest) -> OrderOut:
        cart = self.cart_repo.get_or_create_for_user(user_id)
        if not cart.items:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Your cart is empty.")

        # Lock each variant row to prevent race conditions on inventory.
        locked_variants = {}
        for item in cart.items:
            variant = self.repo.lock_variant(item.variant_id)
            if not variant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="One of the items in your cart no longer exists.",
                )
            if variant.inventory_quantity < item.quantity:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"'{variant.product.name}' ({variant.color_name}, {variant.size}) only has "
                        f"{variant.inventory_quantity} left in stock."
                    ),
                )
            locked_variants[item.id] = variant

        subtotal = sum(
            locked_variants[item.id].product.effective_price * item.quantity for item in cart.items
        )

        coupon_code = payload.coupon_code or cart.coupon_code
        discount_amount = 0.0
        free_shipping = False
        coupon_application = None
        if coupon_code:
            try:
                coupon_application = self.coupons.validate(
                    code=coupon_code, user_id=user_id, items=list(cart.items)
                )
            except CouponError as exc:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
            discount_amount = coupon_application.discount_amount
            free_shipping = coupon_application.free_shipping

        totals = calculate_order_totals(
            subtotal, discount_amount=discount_amount, free_shipping=free_shipping
        )

        order = Order(
            user_id=user_id,
            order_number=self.repo.next_order_number(),
            status=OrderStatus.PAID,
            shipping_address=payload.shipping_address.model_dump(),
            coupon_code=coupon_code if coupon_application else None,
            customer_notes=payload.customer_notes,
            **totals,
        )
        self.db.add(order)
        self.db.flush()

        self.db.add(OrderStatusHistory(order_id=order.id, status=OrderStatus.PAID, note="Order placed."))

        for item in cart.items:
            variant = locked_variants[item.id]
            variant.inventory_quantity -= item.quantity
            self.db.add(
                InventoryTransaction(
                    variant_id=variant.id,
                    change_quantity=-item.quantity,
                    resulting_quantity=variant.inventory_quantity,
                    reason=InventoryChangeReason.ORDER_PLACED,
                    order_id=order.id,
                )
            )
            self.db.add(
                OrderItem(
                    order_id=order.id,
                    variant_id=variant.id,
                    product_name=variant.product.name,
                    variant_size=variant.size,
                    variant_color=variant.color_name,
                    unit_price=variant.product.effective_price,
                    quantity=item.quantity,
                )
            )
            self.db.delete(item)

        if coupon_application:
            self.coupons.record_redemption(coupon_application, user_id=user_id, order_id=order.id)
        cart.coupon_code = None

        self.db.commit()
        persisted_order = self.repo.get_by_id(order.id)
        assert persisted_order is not None
        return _to_order_out(persisted_order)

    def list_orders(self, user_id: uuid.UUID) -> list[OrderSummaryOut]:
        orders = self.repo.list_for_user(user_id)
        return [
            OrderSummaryOut(
                id=o.id,
                order_number=o.order_number,
                status=o.status,
                total=float(o.total),
                item_count=sum(i.quantity for i in o.items),
                created_at=o.created_at,
            )
            for o in orders
        ]

    def get_order(self, user_id: uuid.UUID, order_id: uuid.UUID) -> OrderOut:
        order = self.repo.get_by_id(order_id)
        if not order or order.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
        return _to_order_out(order)

    def cancel_order(self, user_id: uuid.UUID, order_id: uuid.UUID) -> OrderOut:
        order = self.repo.get_by_id(order_id)
        if not order or order.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
        if order.status not in CUSTOMER_CANCELLABLE_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This order can no longer be cancelled - it has already shipped.",
            )

        for item in order.items:
            variant = self.repo.lock_variant(item.variant_id)
            if variant:
                variant.inventory_quantity += item.quantity
                self.db.add(
                    InventoryTransaction(
                        variant_id=variant.id,
                        change_quantity=item.quantity,
                        resulting_quantity=variant.inventory_quantity,
                        reason=InventoryChangeReason.ORDER_CANCELLED,
                        order_id=order.id,
                    )
                )

        order.status = OrderStatus.CANCELLED
        self.db.add(
            OrderStatusHistory(order_id=order.id, status=OrderStatus.CANCELLED, note="Cancelled by customer.")
        )
        self.db.commit()
        persisted_order = self.repo.get_by_id(order.id)
        assert persisted_order is not None
        return _to_order_out(persisted_order)

import { CheckCircle2, Circle } from "lucide-react";
import { Link, useParams } from "react-router-dom";

import { Button } from "@/components/ui/Button";
import { ErrorState } from "@/components/ui/ErrorState";
import { useCancelOrder, useOrder } from "@/hooks/useOrders";
import type { OrderStatus } from "@/types";

function formatUSD(value: number): string {
  return value.toLocaleString("en-US", { style: "currency", currency: "USD" });
}

const STATUS_LABELS: Record<OrderStatus, string> = {
  pending: "Pending",
  paid: "Confirmed",
  processing: "Processing",
  shipped: "Shipped",
  delivered: "Delivered",
  cancelled: "Cancelled",
  returned: "Returned",
};

export function OrderSuccessPage() {
  const { orderId } = useParams<{ orderId: string }>();
  const { data: order, isLoading, isError, refetch } = useOrder(orderId);
  const cancelOrder = useCancelOrder();

  if (isLoading) {
    return (
      <div className="container-veloura py-16">
        <div className="skeleton mx-auto h-64 w-full max-w-2xl rounded-lg" />
      </div>
    );
  }

  if (isError || !order) {
    return (
      <div className="container-veloura py-16">
        <ErrorState title="Order not found" onRetry={() => refetch()} />
      </div>
    );
  }

  return (
    <div className="container-veloura py-16">
      <div className="mx-auto max-w-2xl text-center">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-success/10">
          <CheckCircle2 className="h-7 w-7 text-success" />
        </div>
        <h1 className="mt-5 font-display text-3xl text-ink">Thank you for your order</h1>
        <p className="mt-2 text-sm text-ink-secondary">
          Order <span className="font-medium text-ink">#{order.order_number}</span> has been confirmed.
        </p>

        <div className="mt-8 rounded-lg border border-border bg-surface p-6 text-left">
          <h2 className="mb-4 font-display text-lg text-ink">Order Status</h2>
          <ol className="flex flex-col gap-3">
            {order.status_history.map((entry, i) => (
              <li key={i} className="flex items-start gap-3">
                {i === order.status_history.length - 1 ? (
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-burgundy" />
                ) : (
                  <Circle className="mt-0.5 h-4 w-4 shrink-0 text-ink-secondary/40" />
                )}
                <div>
                  <p className="text-sm font-medium text-ink">{STATUS_LABELS[entry.status]}</p>
                  <p className="text-xs text-ink-secondary">
                    {new Date(entry.created_at).toLocaleString(undefined, {
                      dateStyle: "medium",
                      timeStyle: "short",
                    })}
                    {entry.note ? ` — ${entry.note}` : ""}
                  </p>
                </div>
              </li>
            ))}
          </ol>
          {order.can_cancel && (
            <Button
              variant="secondary"
              size="sm"
              className="mt-4"
              isLoading={cancelOrder.isPending}
              onClick={() => cancelOrder.mutate(order.id)}
            >
              Cancel Order
            </Button>
          )}
        </div>

        <div className="mt-6 rounded-lg border border-border bg-surface p-6 text-left">
          <div className="divide-y divide-border">
            {order.items.map((item) => (
              <div key={item.id} className="flex items-center gap-4 py-4">
                {item.image_url && (
                  <img src={item.image_url} alt="" className="h-16 w-12 rounded object-cover" />
                )}
                <div className="flex-1 text-sm">
                  <p className="font-medium text-ink">{item.product_name}</p>
                  <p className="text-xs text-ink-secondary">
                    {item.variant_color} · {item.variant_size} · Qty {item.quantity}
                  </p>
                </div>
                <span className="text-sm font-medium text-ink">{formatUSD(item.line_total)}</span>
              </div>
            ))}
          </div>
          <div className="mt-4 space-y-2 border-t border-border pt-4 text-sm">
            <div className="flex justify-between">
              <span className="text-ink-secondary">Subtotal</span>
              <span className="text-ink">{formatUSD(order.subtotal)}</span>
            </div>
            {order.discount_amount > 0 && (
              <div className="flex justify-between text-burgundy">
                <span>Discount {order.coupon_code ? `(${order.coupon_code})` : ""}</span>
                <span>-{formatUSD(order.discount_amount)}</span>
              </div>
            )}
            <div className="flex justify-between">
              <span className="text-ink-secondary">Shipping</span>
              <span className="text-ink">{order.shipping_cost === 0 ? "Free" : formatUSD(order.shipping_cost)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-ink-secondary">Tax</span>
              <span className="text-ink">{formatUSD(order.tax)}</span>
            </div>
            <div className="flex justify-between border-t border-border pt-2 text-base font-semibold">
              <span className="text-ink">Total</span>
              <span className="text-ink">{formatUSD(order.total)}</span>
            </div>
          </div>
          {order.customer_notes && (
            <p className="mt-4 border-t border-border pt-4 text-xs text-ink-secondary">
              <span className="font-medium text-ink">Order notes:</span> {order.customer_notes}
            </p>
          )}
        </div>

        <div className="mt-8 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
          <Link to="/account/orders" className="btn-primary">View Order History</Link>
          <Link to="/shop" className="btn-secondary">Continue Shopping</Link>
        </div>
      </div>
    </div>
  );
}

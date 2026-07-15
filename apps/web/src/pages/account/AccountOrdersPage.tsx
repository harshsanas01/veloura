import { Package } from "lucide-react";
import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";
import { useOrders } from "@/hooks/useOrders";
import type { OrderStatus } from "@/types";

const STATUS_VARIANT: Record<OrderStatus, "success" | "warning" | "burgundy" | "error" | "neutral"> = {
  pending: "neutral",
  paid: "burgundy",
  processing: "warning",
  shipped: "burgundy",
  delivered: "success",
  cancelled: "error",
  returned: "neutral",
};

function formatUSD(value: number): string {
  return value.toLocaleString("en-US", { style: "currency", currency: "USD" });
}

export function AccountOrdersPage() {
  const { data: orders, isLoading } = useOrders();

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="skeleton h-20 w-full rounded-lg" />
        ))}
      </div>
    );
  }

  if (!orders || orders.length === 0) {
    return (
      <EmptyState
        icon={Package}
        title="No orders yet"
        description="Once you place an order, it will show up here."
        action={<Link to="/shop" className="btn-primary mt-2">Start Shopping</Link>}
      />
    );
  }

  return (
    <div className="flex flex-col divide-y divide-border rounded-lg border border-border bg-surface">
      {orders.map((order) => (
        <Link
          key={order.id}
          to={`/account/orders/${order.id}`}
          className="flex flex-col gap-2 p-5 transition-colors hover:bg-black/[0.02] sm:flex-row sm:items-center sm:justify-between"
        >
          <div>
            <p className="font-medium text-ink">#{order.order_number}</p>
            <p className="text-xs text-ink-secondary">
              {new Date(order.created_at).toLocaleDateString(undefined, {
                year: "numeric",
                month: "long",
                day: "numeric",
              })}{" "}
              · {order.item_count} item{order.item_count === 1 ? "" : "s"}
            </p>
          </div>
          <div className="flex items-center gap-4">
            <Badge variant={STATUS_VARIANT[order.status]}>{order.status}</Badge>
            <span className="font-medium text-ink">{formatUSD(order.total)}</span>
          </div>
        </Link>
      ))}
    </div>
  );
}

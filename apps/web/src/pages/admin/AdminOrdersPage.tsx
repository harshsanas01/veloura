import { AdminTable } from "@/components/admin/AdminTable";
import { Select } from "@/components/ui/Select";
import { useAdminOrders, useUpdateAdminOrderStatus } from "@/hooks/useAdmin";
import type { AdminOrder, OrderStatus } from "@/types";

const STATUSES: OrderStatus[] = ["pending", "paid", "processing", "shipped", "delivered", "cancelled"];

function formatUSD(value: number): string {
  return value.toLocaleString("en-US", { style: "currency", currency: "USD" });
}

export function AdminOrdersPage() {
  const { data: orders, isLoading } = useAdminOrders();
  const updateStatus = useUpdateAdminOrderStatus();

  return (
    <div>
      <h1 className="font-display text-3xl text-ink">Orders</h1>
      <p className="mt-1 text-sm text-ink-secondary">Manage order fulfillment status.</p>

      <div className="mt-6">
        {isLoading ? (
          <div className="skeleton h-64 w-full rounded-lg" />
        ) : (
          <AdminTable<AdminOrder>
            rows={orders ?? []}
            emptyMessage="No orders yet."
            columns={[
              { header: "Order", render: (o) => <span className="font-medium">#{o.order_number}</span> },
              { header: "Customer", render: (o) => o.customer_email },
              { header: "Items", render: (o) => o.items.length },
              { header: "Total", render: (o) => formatUSD(o.total) },
              {
                header: "Status",
                render: (o) => (
                  <Select
                    aria-label={`Status for order ${o.order_number}`}
                    value={o.status}
                    onChange={(e) =>
                      updateStatus.mutate({ orderId: o.id, status: e.target.value as OrderStatus })
                    }
                    className="w-40"
                  >
                    {STATUSES.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </Select>
                ),
              },
            ]}
          />
        )}
      </div>
    </div>
  );
}

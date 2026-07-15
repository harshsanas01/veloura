import { Search } from "lucide-react";
import { useState } from "react";

import { AdminPagination } from "@/components/admin/AdminPagination";
import { AdminTable } from "@/components/admin/AdminTable";
import { Select } from "@/components/ui/Select";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { useAdminOrders, useUpdateAdminOrderStatus } from "@/hooks/useAdmin";
import type { AdminOrder, OrderStatus } from "@/types";

const PAGE_SIZE = 20;
const STATUSES: OrderStatus[] = [
  "pending",
  "paid",
  "processing",
  "shipped",
  "delivered",
  "cancelled",
  "returned",
];

function formatUSD(value: number): string {
  return value.toLocaleString("en-US", { style: "currency", currency: "USD" });
}

export function AdminOrdersPage() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const debouncedSearch = useDebouncedValue(search, 350);

  const { data, isLoading } = useAdminOrders({ q: debouncedSearch || undefined, page, page_size: PAGE_SIZE });
  const updateStatus = useUpdateAdminOrderStatus();

  return (
    <div>
      <h1 className="font-display text-3xl text-ink">Orders</h1>
      <p className="mt-1 text-sm text-ink-secondary">Manage order fulfillment status.</p>

      <div className="mt-6 flex items-center justify-between gap-4">
        <div className="relative w-full max-w-xs">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-secondary" />
          <input
            type="search"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            placeholder="Search by order # or email..."
            className="input-veloura pl-9"
          />
        </div>
        {data && <span className="text-sm text-ink-secondary">{data.total} orders</span>}
      </div>

      <div className="mt-4">
        {isLoading ? (
          <div className="skeleton h-64 w-full rounded-lg" />
        ) : (
          <AdminTable<AdminOrder>
            rows={data?.items ?? []}
            emptyMessage="No orders found."
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
        {data && <AdminPagination page={data.page} totalPages={data.total_pages} onChange={setPage} />}
      </div>
    </div>
  );
}

import { Link } from "react-router-dom";

import { useAdminDashboard } from "@/hooks/useAdmin";

function formatUSD(value: number): string {
  return value.toLocaleString("en-US", { style: "currency", currency: "USD" });
}

export function AdminOverviewPage() {
  const { data, isLoading } = useAdminDashboard();

  if (isLoading || !data) {
    return (
      <div>
        <h1 className="font-display text-3xl text-ink">Dashboard</h1>
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="skeleton h-24 w-full rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  const stats = [
    { label: "Total Revenue", value: formatUSD(data.total_revenue) },
    { label: "Total Orders", value: data.total_orders },
    { label: "Total Customers", value: data.total_customers },
    { label: "Avg. Order Value", value: formatUSD(data.average_order_value) },
    { label: "Low Stock Variants", value: data.low_stock_variant_count },
    { label: "Out of Stock Variants", value: data.out_of_stock_variant_count },
  ];

  return (
    <div>
      <h1 className="font-display text-3xl text-ink">Dashboard</h1>
      <p className="mt-1 text-sm text-ink-secondary">Overview of your Veloura store.</p>

      <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {stats.map((stat) => (
          <div key={stat.label} className="rounded-lg border border-border bg-surface p-6">
            <span className="text-xs uppercase tracking-wider text-ink-secondary">{stat.label}</span>
            <p className="mt-2 font-display text-3xl text-ink">{stat.value}</p>
          </div>
        ))}
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        <div className="rounded-lg border border-border bg-surface p-6">
          <h2 className="font-display text-xl text-ink">Recent Orders</h2>
          <div className="mt-4 divide-y divide-border">
            {data.recent_orders.length === 0 && <p className="py-4 text-sm text-ink-secondary">No orders yet.</p>}
            {data.recent_orders.map((order) => (
              <div key={order.id} className="flex items-center justify-between py-3 text-sm">
                <div>
                  <p className="font-medium text-ink">#{order.order_number}</p>
                  <p className="text-xs text-ink-secondary">{order.customer_email}</p>
                </div>
                <span className="text-ink-secondary">{order.status}</span>
                <span className="font-medium text-ink">{formatUSD(order.total)}</span>
              </div>
            ))}
          </div>
          <Link to="/admin/orders" className="mt-3 inline-block text-sm text-burgundy hover:text-burgundy-hover">
            View all orders &rarr;
          </Link>
        </div>

        <div className="rounded-lg border border-border bg-surface p-6">
          <h2 className="font-display text-xl text-ink">Best Sellers</h2>
          <div className="mt-4 divide-y divide-border">
            {data.best_selling_products.length === 0 && (
              <p className="py-4 text-sm text-ink-secondary">No sales data yet.</p>
            )}
            {data.best_selling_products.map((p) => (
              <div key={p.product_id} className="flex items-center justify-between py-3 text-sm">
                <span className="font-medium text-ink">{p.name}</span>
                <span className="text-ink-secondary">{p.units_sold} sold</span>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-lg border border-border bg-surface p-6 lg:col-span-2">
          <h2 className="font-display text-xl text-ink">Top Categories</h2>
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            {data.top_categories.length === 0 && (
              <p className="py-4 text-sm text-ink-secondary">No sales data yet.</p>
            )}
            {data.top_categories.map((c) => (
              <div key={c.category_slug} className="rounded border border-border px-4 py-3 text-sm">
                <p className="font-medium text-ink">{c.category_name}</p>
                <p className="text-ink-secondary">{formatUSD(c.revenue)} revenue</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

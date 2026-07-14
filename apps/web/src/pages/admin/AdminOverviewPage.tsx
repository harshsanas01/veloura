import { useAdminOrders, useAdminProducts } from "@/hooks/useAdmin";

function formatUSD(value: number): string {
  return value.toLocaleString("en-US", { style: "currency", currency: "USD" });
}

export function AdminOverviewPage() {
  const { data: products } = useAdminProducts();
  const { data: orders } = useAdminOrders();

  const totalRevenue = orders?.reduce((sum, o) => sum + o.total, 0) ?? 0;
  const lowStockCount =
    products?.reduce(
      (count, p) => count + p.variants.filter((v) => v.inventory_quantity > 0 && v.inventory_quantity <= 3).length,
      0,
    ) ?? 0;

  const stats = [
    { label: "Total Products", value: products?.length ?? "—" },
    { label: "Total Orders", value: orders?.length ?? "—" },
    { label: "Revenue", value: formatUSD(totalRevenue) },
    { label: "Low Stock Variants", value: lowStockCount },
  ];

  return (
    <div>
      <h1 className="font-display text-3xl text-ink">Dashboard</h1>
      <p className="mt-1 text-sm text-ink-secondary">Overview of your Veloura store.</p>

      <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <div key={stat.label} className="rounded-lg border border-border bg-surface p-6">
            <span className="text-xs uppercase tracking-wider text-ink-secondary">{stat.label}</span>
            <p className="mt-2 font-display text-3xl text-ink">{stat.value}</p>
          </div>
        ))}
      </div>

      <div className="mt-8 rounded-lg border border-border bg-surface p-6">
        <h2 className="font-display text-xl text-ink">Recent Orders</h2>
        <div className="mt-4 divide-y divide-border">
          {orders?.slice(0, 5).map((order) => (
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
      </div>
    </div>
  );
}

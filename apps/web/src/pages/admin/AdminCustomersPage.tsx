import { Search } from "lucide-react";
import { useState } from "react";

import { AdminPagination } from "@/components/admin/AdminPagination";
import { AdminTable } from "@/components/admin/AdminTable";
import { Badge } from "@/components/ui/Badge";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { useAdminCustomers } from "@/hooks/useAdmin";
import type { AdminCustomer } from "@/types";

const PAGE_SIZE = 20;

function formatUSD(value: number): string {
  return value.toLocaleString("en-US", { style: "currency", currency: "USD" });
}

export function AdminCustomersPage() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const debouncedSearch = useDebouncedValue(search, 350);
  const { data, isLoading } = useAdminCustomers({ q: debouncedSearch || undefined, page, page_size: PAGE_SIZE });

  return (
    <div>
      <h1 className="font-display text-3xl text-ink">Customers</h1>
      <p className="mt-1 text-sm text-ink-secondary">All registered Veloura accounts.</p>

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
            placeholder="Search by name or email..."
            className="input-veloura pl-9"
          />
        </div>
        {data && <span className="text-sm text-ink-secondary">{data.total} customers</span>}
      </div>

      <div className="mt-4">
        {isLoading ? (
          <div className="skeleton h-64 w-full rounded-lg" />
        ) : (
          <AdminTable<AdminCustomer>
            rows={data?.items ?? []}
            emptyMessage="No customers found."
            columns={[
              { header: "Name", render: (c) => <span className="font-medium">{c.full_name}</span> },
              { header: "Email", render: (c) => c.email },
              { header: "Role", render: (c) => <Badge variant={c.role === "admin" ? "burgundy" : "neutral"}>{c.role}</Badge> },
              { header: "Orders", render: (c) => c.order_count },
              { header: "Total Spent", render: (c) => formatUSD(c.total_spent) },
              {
                header: "Status",
                render: (c) => <Badge variant={c.is_active ? "success" : "neutral"}>{c.is_active ? "Active" : "Inactive"}</Badge>,
              },
              { header: "Joined", render: (c) => new Date(c.created_at).toLocaleDateString() },
            ]}
          />
        )}
        {data && <AdminPagination page={data.page} totalPages={data.total_pages} onChange={setPage} />}
      </div>
    </div>
  );
}

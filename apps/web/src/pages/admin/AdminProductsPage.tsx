import { Plus, Trash2 } from "lucide-react";
import { useState } from "react";

import { AdminTable } from "@/components/admin/AdminTable";
import { ProductFormModal } from "@/components/admin/ProductFormModal";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import {
  useAdminProducts,
  useCreateAdminProduct,
  useDeleteAdminProduct,
  useUpdateAdminProduct,
  useUpdateAdminVariant,
} from "@/hooks/useAdmin";
import type { AdminProduct } from "@/types";

function formatUSD(value: number): string {
  return value.toLocaleString("en-US", { style: "currency", currency: "USD" });
}

export function AdminProductsPage() {
  const { data: products, isLoading } = useAdminProducts();
  const createProduct = useCreateAdminProduct();
  const updateProduct = useUpdateAdminProduct();
  const deleteProduct = useDeleteAdminProduct();
  const updateVariant = useUpdateAdminVariant();

  const [isFormOpen, setFormOpen] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-3xl text-ink">Products</h1>
          <p className="mt-1 text-sm text-ink-secondary">Manage your catalog and inventory.</p>
        </div>
        <Button onClick={() => setFormOpen(true)}>
          <Plus className="h-4 w-4" /> Add Product
        </Button>
      </div>

      <div className="mt-6">
        {isLoading ? (
          <div className="skeleton h-64 w-full rounded-lg" />
        ) : (
          <AdminTable<AdminProduct>
            rows={products ?? []}
            emptyMessage="No products yet."
            columns={[
              { header: "Name", render: (p) => <span className="font-medium">{p.name}</span> },
              { header: "Brand", render: (p) => p.brand },
              { header: "Gender", render: (p) => p.gender },
              { header: "Price", render: (p) => formatUSD(p.sale_price ?? p.base_price) },
              { header: "Variants", render: (p) => p.variants.length },
              {
                header: "Status",
                render: (p) => (
                  <div className="flex gap-1.5">
                    {p.is_featured && <Badge variant="burgundy">Featured</Badge>}
                    <Badge variant={p.is_active ? "success" : "neutral"}>
                      {p.is_active ? "Active" : "Inactive"}
                    </Badge>
                  </div>
                ),
              },
              {
                header: "Actions",
                render: (p) => (
                  <div className="flex items-center gap-3">
                    <button
                      className="text-xs font-medium text-burgundy hover:text-burgundy-hover"
                      onClick={() => setExpandedId(expandedId === p.id ? null : p.id)}
                    >
                      {expandedId === p.id ? "Hide" : "Inventory"}
                    </button>
                    <button
                      className="text-xs font-medium text-ink-secondary hover:text-ink"
                      onClick={() => updateProduct.mutate({ id: p.id, payload: { is_active: !p.is_active } })}
                    >
                      {p.is_active ? "Deactivate" : "Activate"}
                    </button>
                    <button
                      aria-label="Delete product"
                      className="text-ink-secondary hover:text-error"
                      onClick={() => {
                        if (confirm(`Delete "${p.name}"? This cannot be undone.`)) {
                          deleteProduct.mutate(p.id);
                        }
                      }}
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ),
              },
            ]}
          />
        )}
      </div>

      {expandedId && (
        <div className="mt-4 rounded-lg border border-border bg-surface p-5">
          <h3 className="mb-3 font-display text-lg text-ink">
            Inventory — {products?.find((p) => p.id === expandedId)?.name}
          </h3>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {products
              ?.find((p) => p.id === expandedId)
              ?.variants.map((v) => (
                <div key={v.id} className="flex items-center justify-between rounded border border-border px-3 py-2 text-sm">
                  <span className="text-ink-secondary">
                    {v.color_name} · {v.size}
                  </span>
                  <input
                    type="number"
                    min={0}
                    defaultValue={v.inventory_quantity}
                    className="w-20 rounded border border-border px-2 py-1 text-right text-sm"
                    onBlur={(e) => {
                      const value = Number(e.target.value);
                      if (value !== v.inventory_quantity) {
                        updateVariant.mutate({ variantId: v.id, payload: { inventory_quantity: value } });
                      }
                    }}
                  />
                </div>
              ))}
          </div>
        </div>
      )}

      <ProductFormModal
        isOpen={isFormOpen}
        onClose={() => setFormOpen(false)}
        isSubmitting={createProduct.isPending}
        onSubmit={(payload) =>
          createProduct.mutate(payload, { onSuccess: () => setFormOpen(false) })
        }
      />
    </div>
  );
}

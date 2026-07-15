import { Plus, Search, Star, Trash2 } from "lucide-react";
import { useState } from "react";

import { AdminPagination } from "@/components/admin/AdminPagination";
import { AdminTable } from "@/components/admin/AdminTable";
import { ProductFormModal } from "@/components/admin/ProductFormModal";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import {
  useAdminProducts,
  useCreateAdminProduct,
  useDeleteAdminProduct,
  useDeleteAdminVariant,
  useUpdateAdminProduct,
  useUpdateAdminVariant,
} from "@/hooks/useAdmin";
import type { AdminProduct } from "@/types";

const PAGE_SIZE = 20;

function formatUSD(value: number): string {
  return value.toLocaleString("en-US", { style: "currency", currency: "USD" });
}

export function AdminProductsPage() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const debouncedSearch = useDebouncedValue(search, 350);

  const { data, isLoading } = useAdminProducts({ q: debouncedSearch || undefined, page, page_size: PAGE_SIZE });
  const createProduct = useCreateAdminProduct();
  const updateProduct = useUpdateAdminProduct();
  const deleteProduct = useDeleteAdminProduct();
  const updateVariant = useUpdateAdminVariant();
  const deleteVariant = useDeleteAdminVariant();

  const [isFormOpen, setFormOpen] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [deletingProduct, setDeletingProduct] = useState<AdminProduct | null>(null);
  const [deletingVariantId, setDeletingVariantId] = useState<string | null>(null);

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
            placeholder="Search by name or brand..."
            className="input-veloura pl-9"
          />
        </div>
        {data && <span className="text-sm text-ink-secondary">{data.total} products</span>}
      </div>

      <div className="mt-4">
        {isLoading ? (
          <div className="skeleton h-64 w-full rounded-lg" />
        ) : (
          <AdminTable<AdminProduct>
            rows={data?.items ?? []}
            emptyMessage="No products found."
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
                      aria-label={p.is_featured ? "Unfeature product" : "Feature product"}
                      className={p.is_featured ? "text-burgundy" : "text-ink-secondary hover:text-ink"}
                      onClick={() => updateProduct.mutate({ id: p.id, payload: { is_featured: !p.is_featured } })}
                    >
                      <Star className="h-4 w-4" fill={p.is_featured ? "currentColor" : "none"} />
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
                      onClick={() => setDeletingProduct(p)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ),
              },
            ]}
          />
        )}
        {data && <AdminPagination page={data.page} totalPages={data.total_pages} onChange={setPage} />}
      </div>

      {expandedId && (
        <div className="mt-4 rounded-lg border border-border bg-surface p-5">
          <h3 className="mb-3 font-display text-lg text-ink">
            Inventory — {data?.items.find((p) => p.id === expandedId)?.name}
          </h3>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {data?.items
              .find((p) => p.id === expandedId)
              ?.variants.map((v) => (
                <div key={v.id} className="flex items-center justify-between gap-2 rounded border border-border px-3 py-2 text-sm">
                  <span className="text-ink-secondary">
                    {v.color_name} · {v.size}
                  </span>
                  <div className="flex items-center gap-1.5">
                    <input
                      type="number"
                      min={0}
                      defaultValue={v.inventory_quantity}
                      className="w-16 rounded border border-border px-2 py-1 text-right text-sm"
                      onBlur={(e) => {
                        const value = Number(e.target.value);
                        if (value !== v.inventory_quantity) {
                          updateVariant.mutate({ variantId: v.id, payload: { inventory_quantity: value } });
                        }
                      }}
                    />
                    <button
                      aria-label="Delete variant"
                      className="text-ink-secondary hover:text-error"
                      onClick={() => setDeletingVariantId(v.id)}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}

      <ProductFormModal
        isOpen={isFormOpen}
        onClose={() => setFormOpen(false)}
        isSubmitting={createProduct.isPending}
        onSubmit={(payload) => createProduct.mutate(payload, { onSuccess: () => setFormOpen(false) })}
      />

      <ConfirmDialog
        isOpen={Boolean(deletingProduct)}
        onClose={() => setDeletingProduct(null)}
        onConfirm={() =>
          deletingProduct &&
          deleteProduct.mutate(deletingProduct.id, { onSuccess: () => setDeletingProduct(null) })
        }
        title="Delete product?"
        description={`This permanently deletes "${deletingProduct?.name}" and all of its variants. This cannot be undone.`}
        confirmLabel="Delete Product"
        isLoading={deleteProduct.isPending}
      />

      <ConfirmDialog
        isOpen={Boolean(deletingVariantId)}
        onClose={() => setDeletingVariantId(null)}
        onConfirm={() =>
          deletingVariantId &&
          deleteVariant.mutate(deletingVariantId, { onSuccess: () => setDeletingVariantId(null) })
        }
        title="Delete variant?"
        description="This permanently removes this size/color combination. This cannot be undone."
        confirmLabel="Delete Variant"
        isLoading={deleteVariant.isPending}
      />
    </div>
  );
}

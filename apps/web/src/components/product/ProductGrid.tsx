import { PackageSearch } from "lucide-react";

import { ProductCard } from "@/components/product/ProductCard";
import { EmptyState } from "@/components/ui/EmptyState";
import type { ProductListItem } from "@/types";

export function ProductGrid({
  products,
  onClearFilters,
}: {
  products: ProductListItem[];
  onClearFilters?: () => void;
}) {
  if (products.length === 0) {
    return (
      <EmptyState
        icon={PackageSearch}
        title="No products found"
        description="Try adjusting your filters or search terms to find what you're looking for."
        action={
          onClearFilters ? (
            <button onClick={onClearFilters} className="btn-primary mt-2">
              Clear All Filters
            </button>
          ) : undefined
        }
      />
    );
  }

  return (
    <div className="grid grid-cols-2 gap-x-4 gap-y-8 sm:grid-cols-3 lg:grid-cols-4">
      {products.map((product) => (
        <ProductCard key={product.id} product={product} />
      ))}
    </div>
  );
}

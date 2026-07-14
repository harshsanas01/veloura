import { ProductCard } from "@/components/product/ProductCard";
import { ProductSkeleton } from "@/components/product/ProductSkeleton";
import type { ProductListItem } from "@/types";

export function ProductRail({
  products,
  isLoading,
}: {
  products?: ProductListItem[];
  isLoading?: boolean;
}) {
  if (isLoading) {
    return (
      <div className="flex gap-4 overflow-x-auto pb-2 sm:grid sm:grid-cols-3 sm:overflow-visible lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="w-[62vw] shrink-0 sm:w-auto">
            <ProductSkeleton />
          </div>
        ))}
      </div>
    );
  }

  if (!products || products.length === 0) return null;

  return (
    <div className="flex snap-x gap-4 overflow-x-auto pb-2 sm:grid sm:grid-cols-3 sm:overflow-visible sm:pb-0 lg:grid-cols-4">
      {products.map((product) => (
        <div key={product.id} className="w-[62vw] shrink-0 snap-start sm:w-auto">
          <ProductCard product={product} />
        </div>
      ))}
    </div>
  );
}

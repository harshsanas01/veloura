import { SlidersHorizontal } from "lucide-react";
import { useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { FilterSidebar } from "@/components/product/FilterSidebar";
import { MobileFilterDrawer } from "@/components/product/MobileFilterDrawer";
import { ProductGrid } from "@/components/product/ProductGrid";
import { ProductGridSkeleton } from "@/components/product/ProductSkeleton";
import { ErrorState } from "@/components/ui/ErrorState";
import { Select } from "@/components/ui/Select";
import { useProducts } from "@/hooks/useProducts";
import type { Gender, ProductFilters, SortOption } from "@/types";

const PAGE_SIZE = 12;

const TITLES: Record<string, string> = {
  men: "Men's Collection",
  women: "Women's Collection",
};

export function ShopPage({ gender }: { gender?: Gender }) {
  const [searchParams, setSearchParams] = useSearchParams();
  const [mobileFilterOpen, setMobileFilterOpen] = useState(false);

  const filters: ProductFilters = useMemo(
    () => ({
      q: searchParams.get("q") ?? undefined,
      gender: gender ?? (searchParams.get("gender") as Gender | null) ?? undefined,
      category: searchParams.getAll("category").length ? searchParams.getAll("category") : undefined,
      size: searchParams.getAll("size").length ? searchParams.getAll("size") : undefined,
      color: searchParams.getAll("color").length ? searchParams.getAll("color") : undefined,
      min_price: searchParams.get("min_price") ? Number(searchParams.get("min_price")) : undefined,
      max_price: searchParams.get("max_price") ? Number(searchParams.get("max_price")) : undefined,
      sort: (searchParams.get("sort") as SortOption | null) ?? "newest",
      page: searchParams.get("page") ? Number(searchParams.get("page")) : 1,
      page_size: PAGE_SIZE,
    }),
    [searchParams, gender],
  );

  function updateFilters(next: ProductFilters) {
    const params = new URLSearchParams();
    if (next.q) params.set("q", next.q);
    if (!gender && next.gender) params.set("gender", next.gender);
    next.category?.forEach((c) => params.append("category", c));
    next.size?.forEach((s) => params.append("size", s));
    next.color?.forEach((c) => params.append("color", c));
    if (next.min_price !== undefined) params.set("min_price", String(next.min_price));
    if (next.max_price !== undefined) params.set("max_price", String(next.max_price));
    if (next.sort) params.set("sort", next.sort);
    if (next.page && next.page > 1) params.set("page", String(next.page));
    setSearchParams(params);
  }

  const { data, isLoading, isError, refetch } = useProducts(filters);
  const title = gender ? TITLES[gender] : filters.q ? `Results for "${filters.q}"` : "Shop All";

  return (
    <div className="container-veloura py-10">
      <div className="mb-8 flex items-end justify-between">
        <div>
          <h1 className="font-display text-3xl text-ink sm:text-4xl">{title}</h1>
          {data && <p className="mt-1 text-sm text-ink-secondary">{data.total} pieces</p>}
        </div>
        <div className="flex items-center gap-3">
          <button
            className="flex items-center gap-2 rounded border border-border px-3 py-2 text-sm font-medium text-ink lg:hidden"
            onClick={() => setMobileFilterOpen(true)}
          >
            <SlidersHorizontal className="h-4 w-4" />
            Filters
          </button>
          <Select
            aria-label="Sort products"
            value={filters.sort}
            onChange={(e) => updateFilters({ ...filters, sort: e.target.value as SortOption, page: 1 })}
            className="w-44"
          >
            <option value="newest">Newest</option>
            <option value="featured">Featured</option>
            <option value="price_asc">Price: Low to High</option>
            <option value="price_desc">Price: High to Low</option>
            <option value="name_asc">Name: A–Z</option>
          </Select>
        </div>
      </div>

      <div className="grid gap-10 lg:grid-cols-[240px_1fr]">
        <aside className="hidden lg:block">
          <FilterSidebar filters={filters} onChange={updateFilters} />
        </aside>

        <div>
          {isLoading ? (
            <ProductGridSkeleton count={PAGE_SIZE} />
          ) : isError ? (
            <ErrorState onRetry={() => refetch()} description="We couldn't load products. Please try again." />
          ) : (
            <>
              <ProductGrid products={data?.items ?? []} />
              {data && data.total_pages > 1 && (
                <div className="mt-10 flex items-center justify-center gap-2">
                  {Array.from({ length: data.total_pages }).map((_, i) => (
                    <button
                      key={i}
                      onClick={() => updateFilters({ ...filters, page: i + 1 })}
                      className={`h-9 w-9 rounded text-sm font-medium ${
                        (filters.page ?? 1) === i + 1
                          ? "bg-burgundy text-surface"
                          : "text-ink-secondary hover:bg-black/5"
                      }`}
                    >
                      {i + 1}
                    </button>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      </div>

      <MobileFilterDrawer
        isOpen={mobileFilterOpen}
        onClose={() => setMobileFilterOpen(false)}
        filters={filters}
        onChange={updateFilters}
        resultCount={data?.total}
      />
    </div>
  );
}

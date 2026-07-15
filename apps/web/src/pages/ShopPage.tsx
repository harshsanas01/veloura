import { SlidersHorizontal, X } from "lucide-react";
import { useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { Breadcrumbs } from "@/components/ui/Breadcrumbs";
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

const ARRAY_FILTER_KEYS = ["category", "size", "color", "brand", "material", "occasion", "season"] as const;
type ArrayFilterKey = (typeof ARRAY_FILTER_KEYS)[number];

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
      brand: searchParams.getAll("brand").length ? searchParams.getAll("brand") : undefined,
      material: searchParams.getAll("material").length ? searchParams.getAll("material") : undefined,
      occasion: searchParams.getAll("occasion").length ? searchParams.getAll("occasion") : undefined,
      season: searchParams.getAll("season").length ? searchParams.getAll("season") : undefined,
      min_price: searchParams.get("min_price") ? Number(searchParams.get("min_price")) : undefined,
      max_price: searchParams.get("max_price") ? Number(searchParams.get("max_price")) : undefined,
      in_stock_only: searchParams.get("in_stock_only") === "1" || undefined,
      sale_only: searchParams.get("sale_only") === "1" || undefined,
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
    next.brand?.forEach((b) => params.append("brand", b));
    next.material?.forEach((m) => params.append("material", m));
    next.occasion?.forEach((o) => params.append("occasion", o));
    next.season?.forEach((s) => params.append("season", s));
    if (next.min_price !== undefined) params.set("min_price", String(next.min_price));
    if (next.max_price !== undefined) params.set("max_price", String(next.max_price));
    if (next.in_stock_only) params.set("in_stock_only", "1");
    if (next.sale_only) params.set("sale_only", "1");
    if (next.sort) params.set("sort", next.sort);
    if (next.page && next.page > 1) params.set("page", String(next.page));
    setSearchParams(params);
  }

  function clearAllFilters() {
    updateFilters({ gender: filters.gender, sort: filters.sort, page: 1, page_size: filters.page_size });
  }

  function removeChip(key: ArrayFilterKey, value: string) {
    const current = filters[key] ?? [];
    updateFilters({ ...filters, [key]: current.filter((v) => v !== value) || undefined, page: 1 });
  }

  const { data, isLoading, isError, refetch } = useProducts(filters);
  const title = gender ? TITLES[gender] : filters.q ? `Results for "${filters.q}"` : "Shop All";

  const chips: { key: ArrayFilterKey | "price" | "in_stock_only" | "sale_only"; label: string; onRemove: () => void }[] = [];
  for (const key of ARRAY_FILTER_KEYS) {
    if (key === "category" && gender) continue;
    for (const value of filters[key] ?? []) {
      chips.push({ key, label: value, onRemove: () => removeChip(key, value) });
    }
  }
  if (filters.min_price !== undefined || filters.max_price !== undefined) {
    chips.push({
      key: "price",
      label: `$${filters.min_price ?? 0} – $${filters.max_price ?? "∞"}`,
      onRemove: () => updateFilters({ ...filters, min_price: undefined, max_price: undefined, page: 1 }),
    });
  }
  if (filters.in_stock_only) {
    chips.push({
      key: "in_stock_only",
      label: "In stock only",
      onRemove: () => updateFilters({ ...filters, in_stock_only: undefined, page: 1 }),
    });
  }
  if (filters.sale_only) {
    chips.push({
      key: "sale_only",
      label: "On sale",
      onRemove: () => updateFilters({ ...filters, sale_only: undefined, page: 1 }),
    });
  }

  return (
    <div className="container-veloura py-10">
      <Breadcrumbs
        items={[
          { label: "Home", to: "/" },
          { label: "Shop", to: gender ? "/shop" : undefined },
          ...(gender ? [{ label: gender === "men" ? "Men" : "Women" }] : []),
        ]}
      />

      <div className="mb-6 flex items-end justify-between">
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
            className="w-48"
          >
            <option value="newest">Newest</option>
            <option value="featured">Featured</option>
            <option value="price_asc">Price: Low to High</option>
            <option value="price_desc">Price: High to Low</option>
            <option value="biggest_discount">Biggest Discount</option>
            <option value="name_asc">Name: A–Z</option>
          </Select>
        </div>
      </div>

      {chips.length > 0 && (
        <div className="mb-8 flex flex-wrap items-center gap-2">
          {chips.map((chip) => (
            <button
              key={`${chip.key}-${chip.label}`}
              onClick={chip.onRemove}
              className="flex items-center gap-1.5 rounded-full bg-rose/40 px-3 py-1.5 text-xs font-medium capitalize text-burgundy transition-colors hover:bg-rose/70"
            >
              {chip.label}
              <X className="h-3 w-3" />
            </button>
          ))}
          <button onClick={clearAllFilters} className="text-xs font-medium text-ink-secondary hover:text-ink">
            Clear all
          </button>
        </div>
      )}

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
              <ProductGrid products={data?.items ?? []} onClearFilters={clearAllFilters} />
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

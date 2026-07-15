import { Search } from "lucide-react";
import { useEffect, useState } from "react";

import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { useCategories, useFacets } from "@/hooks/useProducts";
import type { ProductFilters } from "@/types";
import { cn } from "@/utils/cn";

const SIZES = ["XS", "S", "M", "L", "XL", "XXL"];
const COLORS = [
  { name: "Black", hex: "#111111" },
  { name: "White", hex: "#FAFAFA" },
  { name: "Navy", hex: "#1B2A4A" },
  { name: "Burgundy", hex: "#6E1835" },
  { name: "Olive", hex: "#5C6B4A" },
  { name: "Camel", hex: "#C19A6B" },
  { name: "Charcoal", hex: "#36454F" },
  { name: "Cream", hex: "#F5EFE6" },
];
const SEASON_LABELS: Record<string, string> = {
  spring: "Spring",
  summer: "Summer",
  fall: "Fall",
  winter: "Winter",
};

interface FilterSidebarProps {
  filters: ProductFilters;
  onChange: (filters: ProductFilters) => void;
}

export function FilterSidebar({ filters, onChange }: FilterSidebarProps) {
  const { data: categories } = useCategories();
  const { data: facets } = useFacets();

  const [searchText, setSearchText] = useState(filters.q ?? "");
  const debouncedSearch = useDebouncedValue(searchText, 350);

  useEffect(() => setSearchText(filters.q ?? ""), [filters.q]);

  useEffect(() => {
    if (debouncedSearch !== (filters.q ?? "")) {
      onChange({ ...filters, q: debouncedSearch || undefined, page: 1 });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedSearch]);

  function toggleArrayValue(key: "category" | "size" | "color" | "brand" | "material" | "occasion" | "season", value: string) {
    const current = filters[key] ?? [];
    const next = current.includes(value) ? current.filter((v) => v !== value) : [...current, value];
    onChange({ ...filters, [key]: next.length ? next : undefined, page: 1 });
  }

  return (
    <div className="flex flex-col gap-8">
      <FilterGroup title="Search">
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-secondary" />
          <input
            type="search"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            placeholder="Search products, brands, colors..."
            aria-label="Search products"
            className="input-veloura pl-9"
          />
        </div>
      </FilterGroup>

      <FilterGroup title="Category">
        <div className="flex flex-col gap-2">
          {categories?.map((cat) => (
            <label key={cat.slug} className="flex cursor-pointer items-center gap-2.5 text-sm text-ink-secondary hover:text-ink">
              <input
                type="checkbox"
                checked={filters.category?.includes(cat.slug) ?? false}
                onChange={() => toggleArrayValue("category", cat.slug)}
                className="h-4 w-4 rounded border-border accent-burgundy"
              />
              {cat.name}
            </label>
          ))}
        </div>
      </FilterGroup>

      <FilterGroup title="Price">
        <div className="flex items-center gap-3">
          <input
            type="number"
            min={0}
            placeholder="Min"
            value={filters.min_price ?? ""}
            onChange={(e) =>
              onChange({
                ...filters,
                min_price: e.target.value ? Number(e.target.value) : undefined,
                page: 1,
              })
            }
            className="input-veloura"
          />
          <span className="text-ink-secondary">&ndash;</span>
          <input
            type="number"
            min={0}
            placeholder="Max"
            value={filters.max_price ?? ""}
            onChange={(e) =>
              onChange({
                ...filters,
                max_price: e.target.value ? Number(e.target.value) : undefined,
                page: 1,
              })
            }
            className="input-veloura"
          />
        </div>
        {facets && (
          <input
            type="range"
            min={Math.floor(facets.min_price)}
            max={Math.ceil(facets.max_price)}
            value={filters.max_price ?? Math.ceil(facets.max_price)}
            onChange={(e) => onChange({ ...filters, max_price: Number(e.target.value), page: 1 })}
            className="mt-3 w-full accent-burgundy"
            aria-label="Maximum price"
          />
        )}
      </FilterGroup>

      <FilterGroup title="Size">
        <div className="flex flex-wrap gap-2">
          {SIZES.map((size) => {
            const active = filters.size?.includes(size) ?? false;
            return (
              <button
                key={size}
                onClick={() => toggleArrayValue("size", size)}
                className={cn(
                  "min-w-[2.5rem] rounded border px-2.5 py-1.5 text-xs font-medium transition-colors",
                  active ? "border-burgundy bg-burgundy text-surface" : "border-border text-ink hover:border-ink",
                )}
              >
                {size}
              </button>
            );
          })}
        </div>
      </FilterGroup>

      <FilterGroup title="Color">
        <div className="flex flex-wrap gap-2">
          {COLORS.map((color) => {
            const active = filters.color?.includes(color.name) ?? false;
            return (
              <button
                key={color.name}
                title={color.name}
                aria-label={color.name}
                onClick={() => toggleArrayValue("color", color.name)}
                className={cn(
                  "flex h-8 w-8 items-center justify-center rounded-full border-2",
                  active ? "border-burgundy" : "border-transparent hover:border-taupe",
                )}
              >
                <span
                  className="h-6 w-6 rounded-full border border-black/10"
                  style={{ backgroundColor: color.hex }}
                />
              </button>
            );
          })}
        </div>
      </FilterGroup>

      {facets && facets.brands.length > 0 && (
        <FilterGroup title="Brand">
          <div className="flex max-h-48 flex-col gap-2 overflow-y-auto pr-1">
            {facets.brands.map((brand) => (
              <label key={brand} className="flex cursor-pointer items-center gap-2.5 text-sm text-ink-secondary hover:text-ink">
                <input
                  type="checkbox"
                  checked={filters.brand?.includes(brand) ?? false}
                  onChange={() => toggleArrayValue("brand", brand)}
                  className="h-4 w-4 rounded border-border accent-burgundy"
                />
                {brand}
              </label>
            ))}
          </div>
        </FilterGroup>
      )}

      {facets && facets.materials.length > 0 && (
        <FilterGroup title="Material">
          <div className="flex max-h-48 flex-col gap-2 overflow-y-auto pr-1">
            {facets.materials.map((material) => (
              <label key={material} className="flex cursor-pointer items-center gap-2.5 text-sm capitalize text-ink-secondary hover:text-ink">
                <input
                  type="checkbox"
                  checked={filters.material?.includes(material) ?? false}
                  onChange={() => toggleArrayValue("material", material)}
                  className="h-4 w-4 rounded border-border accent-burgundy"
                />
                {material}
              </label>
            ))}
          </div>
        </FilterGroup>
      )}

      {facets && facets.occasions.length > 0 && (
        <FilterGroup title="Occasion">
          <div className="flex flex-wrap gap-2">
            {facets.occasions.map((occasion) => {
              const active = filters.occasion?.includes(occasion) ?? false;
              return (
                <button
                  key={occasion}
                  onClick={() => toggleArrayValue("occasion", occasion)}
                  className={cn(
                    "rounded-full border px-3 py-1.5 text-xs font-medium capitalize transition-colors",
                    active ? "border-burgundy bg-burgundy text-surface" : "border-border text-ink hover:border-ink",
                  )}
                >
                  {occasion.replace("-", " ")}
                </button>
              );
            })}
          </div>
        </FilterGroup>
      )}

      {facets && facets.seasons.length > 0 && (
        <FilterGroup title="Season">
          <div className="flex flex-wrap gap-2">
            {facets.seasons.map((season) => {
              const active = filters.season?.includes(season) ?? false;
              return (
                <button
                  key={season}
                  onClick={() => toggleArrayValue("season", season)}
                  className={cn(
                    "rounded-full border px-3 py-1.5 text-xs font-medium transition-colors",
                    active ? "border-burgundy bg-burgundy text-surface" : "border-border text-ink hover:border-ink",
                  )}
                >
                  {SEASON_LABELS[season] ?? season}
                </button>
              );
            })}
          </div>
        </FilterGroup>
      )}

      <FilterGroup title="Availability">
        <div className="flex flex-col gap-2">
          <label className="flex cursor-pointer items-center gap-2.5 text-sm text-ink-secondary hover:text-ink">
            <input
              type="checkbox"
              checked={filters.in_stock_only ?? false}
              onChange={(e) => onChange({ ...filters, in_stock_only: e.target.checked || undefined, page: 1 })}
              className="h-4 w-4 rounded border-border accent-burgundy"
            />
            In stock only
          </label>
          <label className="flex cursor-pointer items-center gap-2.5 text-sm text-ink-secondary hover:text-ink">
            <input
              type="checkbox"
              checked={filters.sale_only ?? false}
              onChange={(e) => onChange({ ...filters, sale_only: e.target.checked || undefined, page: 1 })}
              className="h-4 w-4 rounded border-border accent-burgundy"
            />
            On sale only
          </label>
        </div>
      </FilterGroup>

      <button
        onClick={() =>
          onChange({ gender: filters.gender, sort: filters.sort, page: 1, page_size: filters.page_size })
        }
        className="text-left text-sm font-medium text-burgundy hover:text-burgundy-hover"
      >
        Clear all filters
      </button>
    </div>
  );
}

function FilterGroup({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-ink">{title}</h3>
      {children}
    </div>
  );
}

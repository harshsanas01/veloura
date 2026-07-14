import { useCategories } from "@/hooks/useProducts";
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

interface FilterSidebarProps {
  filters: ProductFilters;
  onChange: (filters: ProductFilters) => void;
}

export function FilterSidebar({ filters, onChange }: FilterSidebarProps) {
  const { data: categories } = useCategories();

  function toggleArrayValue(key: "category" | "size" | "color", value: string) {
    const current = filters[key] ?? [];
    const next = current.includes(value)
      ? current.filter((v) => v !== value)
      : [...current, value];
    onChange({ ...filters, [key]: next.length ? next : undefined, page: 1 });
  }

  return (
    <div className="flex flex-col gap-8">
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

import { cn } from "@/utils/cn";

export function SizeSelector({
  sizes,
  selected,
  onSelect,
  availableSizes,
}: {
  sizes: string[];
  selected: string | null;
  onSelect: (size: string) => void;
  availableSizes?: Set<string>;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {sizes.map((size) => {
        const isSelected = selected === size;
        const isAvailable = availableSizes ? availableSizes.has(size) : true;
        return (
          <button
            key={size}
            type="button"
            disabled={!isAvailable}
            aria-pressed={isSelected}
            onClick={() => onSelect(size)}
            className={cn(
              "min-w-[2.75rem] rounded border px-3 py-2 text-sm font-medium transition-colors",
              isSelected
                ? "border-burgundy bg-burgundy text-surface"
                : "border-border bg-surface text-ink hover:border-ink",
              !isAvailable && "cursor-not-allowed border-border/60 text-ink-secondary/40 line-through hover:border-border/60",
            )}
          >
            {size}
          </button>
        );
      })}
    </div>
  );
}

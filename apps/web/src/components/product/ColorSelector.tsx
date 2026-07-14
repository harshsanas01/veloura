import { Check } from "lucide-react";

import type { ProductColor } from "@/types";
import { cn } from "@/utils/cn";

export function ColorSelector({
  colors,
  selected,
  onSelect,
}: {
  colors: ProductColor[];
  selected: string | null;
  onSelect: (colorName: string) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {colors.map((color) => {
        const isSelected = selected === color.name;
        return (
          <button
            key={color.name}
            type="button"
            title={color.name}
            aria-label={`Select color ${color.name}`}
            aria-pressed={isSelected}
            onClick={() => onSelect(color.name)}
            className={cn(
              "flex h-9 w-9 items-center justify-center rounded-full border-2 transition-all",
              isSelected ? "border-burgundy" : "border-transparent hover:border-taupe",
            )}
          >
            <span
              className="flex h-7 w-7 items-center justify-center rounded-full border border-black/10"
              style={{ backgroundColor: color.hex }}
            >
              {isSelected && (
                <Check
                  className="h-3.5 w-3.5"
                  style={{ color: isLight(color.hex) ? "#181613" : "#FFFDFC" }}
                />
              )}
            </span>
          </button>
        );
      })}
    </div>
  );
}

function isLight(hex: string): boolean {
  const c = hex.replace("#", "");
  if (c.length !== 6) return true;
  const r = parseInt(c.slice(0, 2), 16);
  const g = parseInt(c.slice(2, 4), 16);
  const b = parseInt(c.slice(4, 6), 16);
  return (r * 299 + g * 587 + b * 114) / 1000 > 150;
}

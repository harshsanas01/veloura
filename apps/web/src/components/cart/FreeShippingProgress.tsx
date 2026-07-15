import { Truck } from "lucide-react";

export function FreeShippingProgress({ remaining, subtotal }: { remaining: number; subtotal: number }) {
  if (remaining <= 0) {
    return (
      <div className="flex items-center gap-2 rounded bg-success/10 px-3 py-2 text-xs font-medium text-success">
        <Truck className="h-4 w-4 shrink-0" />
        You've unlocked free shipping!
      </div>
    );
  }

  const threshold = subtotal + remaining;
  const progress = Math.min(100, Math.round((subtotal / threshold) * 100));

  return (
    <div className="flex flex-col gap-1.5">
      <p className="text-xs text-ink-secondary">
        Add <span className="font-medium text-ink">${remaining.toFixed(2)}</span> more for free shipping
      </p>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-taupe/30">
        <div className="h-full rounded-full bg-burgundy transition-all" style={{ width: `${progress}%` }} />
      </div>
    </div>
  );
}

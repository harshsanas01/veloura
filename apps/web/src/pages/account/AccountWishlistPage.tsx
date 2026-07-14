import { Heart, X } from "lucide-react";
import { Link } from "react-router-dom";

import { EmptyState } from "@/components/ui/EmptyState";
import { useToggleWishlist, useWishlist } from "@/hooks/useWishlist";

function formatUSD(value: number): string {
  return value.toLocaleString("en-US", { style: "currency", currency: "USD" });
}

export function AccountWishlistPage() {
  const { data: wishlist, isLoading } = useWishlist();
  const { remove } = useToggleWishlist();

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="skeleton aspect-[3/4] w-full rounded-lg" />
        ))}
      </div>
    );
  }

  if (!wishlist || wishlist.items.length === 0) {
    return (
      <EmptyState
        icon={Heart}
        title="Your wishlist is empty"
        description="Save pieces you love while browsing to find them here later."
        action={<Link to="/shop" className="btn-primary mt-2">Discover Products</Link>}
      />
    );
  }

  return (
    <div className="grid grid-cols-2 gap-x-4 gap-y-8 sm:grid-cols-3">
      {wishlist.items.map((item) => (
        <div key={item.id} className="group relative">
          <Link to={`/products/${item.slug}`}>
            <div className="relative aspect-[3/4] overflow-hidden rounded-lg bg-taupe/10">
              <img src={item.primary_image} alt={item.name} className="h-full w-full object-cover" />
              {!item.in_stock && (
                <span className="absolute left-3 top-3 rounded-full bg-ink/80 px-3 py-1 text-[11px] font-semibold uppercase tracking-wider text-surface">
                  Sold Out
                </span>
              )}
            </div>
          </Link>
          <button
            aria-label="Remove from wishlist"
            onClick={() => remove.mutate(item.product_id)}
            className="absolute right-3 top-3 flex h-8 w-8 items-center justify-center rounded-full bg-surface/90 text-ink shadow-card hover:text-error"
          >
            <X className="h-4 w-4" />
          </button>
          <div className="mt-3">
            <span className="text-[11px] uppercase tracking-wider text-ink-secondary">{item.brand}</span>
            <Link to={`/products/${item.slug}`} className="block text-sm font-medium text-ink hover:text-burgundy">
              {item.name}
            </Link>
            <span className="text-sm text-ink">{formatUSD(item.effective_price)}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

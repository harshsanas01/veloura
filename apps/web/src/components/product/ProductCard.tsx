import { motion } from "framer-motion";
import { Heart } from "lucide-react";
import { Link } from "react-router-dom";

import { PriceDisplay } from "@/components/product/PriceDisplay";
import { useAuthStore } from "@/store/authStore";
import { useToggleWishlist } from "@/hooks/useWishlist";
import type { ProductListItem } from "@/types";
import { cn } from "@/utils/cn";

export function ProductCard({ product }: { product: ProductListItem }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const { add } = useToggleWishlist();

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="group relative flex w-full flex-shrink-0 flex-col"
    >
      <Link to={`/products/${product.slug}`} className="block">
        <div className="relative aspect-[3/4] overflow-hidden rounded-lg bg-taupe/10">
          <img
            src={product.primary_image}
            alt={product.name}
            loading="lazy"
            className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
          />
          {!product.in_stock && (
            <span className="absolute left-3 top-3 rounded-full bg-ink/80 px-3 py-1 text-[11px] font-semibold uppercase tracking-wider text-surface">
              Sold Out
            </span>
          )}
          {product.sale_price && product.in_stock && (
            <span className="absolute left-3 top-3 rounded-full bg-burgundy px-3 py-1 text-[11px] font-semibold uppercase tracking-wider text-surface">
              Sale
            </span>
          )}
          {isAuthenticated && (
            <button
              type="button"
              aria-label="Add to wishlist"
              onClick={(e) => {
                e.preventDefault();
                add.mutate(product.id);
              }}
              className="absolute right-3 top-3 flex h-9 w-9 items-center justify-center rounded-full bg-surface/90 text-ink opacity-0 shadow-card transition-opacity group-hover:opacity-100 hover:text-burgundy"
            >
              <Heart className="h-4 w-4" />
            </button>
          )}
        </div>
      </Link>
      <div className="mt-3 flex flex-col gap-1">
        <span className="text-[11px] uppercase tracking-wider text-ink-secondary">{product.brand}</span>
        <Link to={`/products/${product.slug}`} className="text-sm font-medium text-ink hover:text-burgundy">
          {product.name}
        </Link>
        <PriceDisplay basePrice={product.base_price} salePrice={product.sale_price} size="sm" />
        <div className="mt-1 flex gap-1.5">
          {product.available_colors.slice(0, 5).map((hex) => (
            <span
              key={hex}
              className={cn("h-3.5 w-3.5 rounded-full border border-black/10")}
              style={{ backgroundColor: hex }}
            />
          ))}
        </div>
      </div>
    </motion.div>
  );
}

import { motion } from "framer-motion";
import { ShoppingBag, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/Button";
import { useAddToCart } from "@/hooks/useCart";
import type { StylistOutfit } from "@/types";

function formatUSD(value: number): string {
  return value.toLocaleString("en-US", { style: "currency", currency: "USD" });
}

export function OutfitCard({ outfit }: { outfit: StylistOutfit }) {
  const addToCart = useAddToCart();

  function addWholeOutfit() {
    outfit.items.forEach((item, i) => {
      setTimeout(() => addToCart.mutate({ variantId: item.variant_id }), i * 150);
    });
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="overflow-hidden rounded-lg border border-border bg-surface shadow-card"
    >
      <div className="flex items-center justify-between border-b border-border bg-rose/20 px-5 py-3">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-burgundy" />
          <span className="font-display text-lg text-ink">{outfit.name}</span>
        </div>
        <span className="text-sm font-semibold text-burgundy">{formatUSD(outfit.total_price)}</span>
      </div>

      <p className="px-5 pt-4 text-sm text-ink-secondary">{outfit.explanation}</p>

      <div className="grid grid-cols-2 gap-4 p-5 sm:grid-cols-3">
        {outfit.items.map((item) => (
          <div key={item.variant_id} className="flex flex-col gap-2">
            <Link to={`/products/${item.product_slug}`} className="block overflow-hidden rounded-lg bg-taupe/10">
              <img
                src={item.image_url}
                alt={item.product_name}
                className="aspect-[3/4] w-full object-cover transition-transform hover:scale-105"
              />
            </Link>
            <div>
              <span className="text-[10px] uppercase tracking-wider text-ink-secondary">{item.brand}</span>
              <Link to={`/products/${item.product_slug}`} className="block text-xs font-medium text-ink hover:text-burgundy">
                {item.product_name}
              </Link>
              <span className="text-xs text-ink-secondary">{item.color_name} · {item.size}</span>
              <p className="mt-0.5 text-xs font-medium text-ink">{formatUSD(item.price)}</p>
            </div>
            <button
              onClick={() => addToCart.mutate({ variantId: item.variant_id })}
              className="flex items-center justify-center gap-1 rounded border border-border py-1.5 text-[11px] font-medium text-ink hover:border-burgundy hover:text-burgundy"
            >
              <ShoppingBag className="h-3 w-3" /> Add
            </button>
          </div>
        ))}
      </div>

      <div className="border-t border-border px-5 py-4">
        <Button className="w-full" onClick={addWholeOutfit} isLoading={addToCart.isPending}>
          <ShoppingBag className="h-4 w-4" /> Add Complete Outfit — {formatUSD(outfit.total_price)}
        </Button>
      </div>
    </motion.div>
  );
}

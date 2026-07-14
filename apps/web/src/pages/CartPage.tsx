import { Minus, Plus, ShoppingBag, Trash2 } from "lucide-react";
import { Link } from "react-router-dom";

import { EmptyState } from "@/components/ui/EmptyState";
import { useCart, useRemoveCartItem, useUpdateCartItem } from "@/hooks/useCart";

function formatUSD(value: number): string {
  return value.toLocaleString("en-US", { style: "currency", currency: "USD" });
}

export function CartPage() {
  const { data: cart, isLoading } = useCart();
  const updateItem = useUpdateCartItem();
  const removeItem = useRemoveCartItem();

  return (
    <div className="container-veloura py-10">
      <h1 className="font-display text-3xl text-ink">Your Bag</h1>

      {isLoading ? (
        <div className="mt-8 space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="skeleton h-32 w-full rounded-lg" />
          ))}
        </div>
      ) : !cart || cart.items.length === 0 ? (
        <div className="mt-8">
          <EmptyState
            icon={ShoppingBag}
            title="Your bag is empty"
            description="Explore the collection and add pieces you love."
            action={
              <Link to="/shop" className="btn-primary mt-2">
                Shop the Collection
              </Link>
            }
          />
        </div>
      ) : (
        <div className="mt-8 grid gap-10 lg:grid-cols-[1fr_360px]">
          <div className="divide-y divide-border">
            {cart.items.map((item) => (
              <div key={item.id} className="flex gap-5 py-6">
                <Link to={`/products/${item.variant.product_slug}`} className="shrink-0">
                  <img
                    src={item.variant.image_url}
                    alt={item.variant.product_name}
                    className="h-32 w-24 rounded object-cover"
                  />
                </Link>
                <div className="flex flex-1 flex-col gap-1.5">
                  <span className="text-xs uppercase tracking-wider text-ink-secondary">
                    {item.variant.product_brand}
                  </span>
                  <Link
                    to={`/products/${item.variant.product_slug}`}
                    className="font-medium text-ink hover:text-burgundy"
                  >
                    {item.variant.product_name}
                  </Link>
                  <span className="text-sm text-ink-secondary">
                    {item.variant.color_name} · Size {item.variant.size}
                  </span>
                  <div className="mt-2 flex items-center justify-between">
                    <div className="flex items-center rounded border border-border">
                      <button
                        aria-label="Decrease quantity"
                        className="flex h-9 w-9 items-center justify-center disabled:opacity-30"
                        disabled={item.quantity <= 1}
                        onClick={() => updateItem.mutate({ itemId: item.id, quantity: item.quantity - 1 })}
                      >
                        <Minus className="h-3.5 w-3.5" />
                      </button>
                      <span className="w-8 text-center text-sm tabular-nums">{item.quantity}</span>
                      <button
                        aria-label="Increase quantity"
                        className="flex h-9 w-9 items-center justify-center disabled:opacity-30"
                        disabled={item.quantity >= item.variant.inventory_quantity}
                        onClick={() => updateItem.mutate({ itemId: item.id, quantity: item.quantity + 1 })}
                      >
                        <Plus className="h-3.5 w-3.5" />
                      </button>
                    </div>
                    <span className="font-medium text-ink">{formatUSD(item.line_total)}</span>
                  </div>
                </div>
                <button
                  aria-label="Remove item"
                  onClick={() => removeItem.mutate(item.id)}
                  className="self-start text-ink-secondary hover:text-error"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>

          <div className="h-fit rounded-lg border border-border bg-surface p-6">
            <h2 className="font-display text-xl text-ink">Order Summary</h2>
            <div className="mt-4 flex justify-between text-sm">
              <span className="text-ink-secondary">Subtotal</span>
              <span className="font-medium text-ink">{formatUSD(cart.subtotal)}</span>
            </div>
            <p className="mt-1 text-xs text-ink-secondary">Shipping and tax calculated at checkout.</p>
            <Link to="/checkout" className="btn-primary mt-5 w-full">
              Proceed to Checkout
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}

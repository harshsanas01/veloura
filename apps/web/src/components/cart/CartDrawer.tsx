import { Minus, Plus, ShoppingBag, Trash2 } from "lucide-react";
import { Link } from "react-router-dom";

import { FreeShippingProgress } from "@/components/cart/FreeShippingProgress";
import { Drawer } from "@/components/ui/Drawer";
import { EmptyState } from "@/components/ui/EmptyState";
import { useUnifiedCart } from "@/hooks/useUnifiedCart";
import { useUIStore } from "@/store/uiStore";

function formatUSD(value: number): string {
  return value.toLocaleString("en-US", { style: "currency", currency: "USD" });
}

export function CartDrawer() {
  const isOpen = useUIStore((s) => s.isCartOpen);
  const closeCart = useUIStore((s) => s.closeCart);
  const cart = useUnifiedCart();

  return (
    <Drawer isOpen={isOpen} onClose={closeCart} title="Your Bag">
      <div className="flex h-full flex-col">
        {cart.isLoading ? (
          <div className="flex-1 space-y-4 p-6">
            {[1, 2].map((i) => (
              <div key={i} className="skeleton h-24 w-full rounded" />
            ))}
          </div>
        ) : cart.items.length === 0 ? (
          <div className="flex-1 p-6">
            <EmptyState
              icon={ShoppingBag}
              title="Your bag is empty"
              description="Explore the collection and add pieces you love."
              action={
                <Link to="/shop" onClick={closeCart} className="btn-primary mt-2">
                  Shop the Collection
                </Link>
              }
            />
          </div>
        ) : (
          <>
            <div className="flex-1 divide-y divide-border overflow-y-auto px-6">
              {cart.items.map((item) => (
                <div key={item.id} className="flex gap-4 py-5">
                  <img src={item.image} alt={item.name} className="h-24 w-20 rounded object-cover" />
                  <div className="flex flex-1 flex-col gap-1">
                    <Link
                      to={`/products/${item.slug}`}
                      onClick={closeCart}
                      className="text-sm font-medium text-ink hover:text-burgundy"
                    >
                      {item.name}
                    </Link>
                    <span className="text-xs text-ink-secondary">
                      {item.color} · {item.size}
                    </span>
                    <div className="mt-1 flex items-center justify-between">
                      <div className="flex items-center rounded border border-border">
                        <button
                          aria-label="Decrease quantity"
                          className="flex h-7 w-7 items-center justify-center disabled:opacity-30"
                          disabled={item.quantity <= 1}
                          onClick={() => cart.updateQuantity(item.id, item.quantity - 1)}
                        >
                          <Minus className="h-3 w-3" />
                        </button>
                        <span className="w-6 text-center text-xs tabular-nums">{item.quantity}</span>
                        <button
                          aria-label="Increase quantity"
                          className="flex h-7 w-7 items-center justify-center disabled:opacity-30"
                          disabled={item.quantity >= item.inventoryQuantity}
                          onClick={() => cart.updateQuantity(item.id, item.quantity + 1)}
                        >
                          <Plus className="h-3 w-3" />
                        </button>
                      </div>
                      <span className="text-sm font-medium text-ink">{formatUSD(item.lineTotal)}</span>
                    </div>
                  </div>
                  <button
                    aria-label="Remove item"
                    onClick={() => cart.removeItem(item.id)}
                    className="self-start text-ink-secondary hover:text-error"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
            <div className="border-t border-border px-6 py-5">
              <div className="mb-4">
                <FreeShippingProgress remaining={cart.freeShippingRemaining} subtotal={cart.subtotal} />
              </div>
              <div className="mb-4 flex items-center justify-between text-sm">
                <span className="text-ink-secondary">Subtotal</span>
                <span className="font-semibold text-ink">{formatUSD(cart.subtotal)}</span>
              </div>
              {cart.isGuest && (
                <p className="mb-3 text-xs text-ink-secondary">
                  Sign in at checkout to apply coupons and see your final total.
                </p>
              )}
              <Link to="/checkout" onClick={closeCart} className="btn-primary w-full">
                Checkout
              </Link>
              <Link to="/cart" onClick={closeCart} className="btn-ghost mt-2 w-full">
                View Bag
              </Link>
            </div>
          </>
        )}
      </div>
    </Drawer>
  );
}

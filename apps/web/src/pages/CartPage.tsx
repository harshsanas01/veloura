import { Heart, Minus, Plus, ShoppingBag, Trash2 } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";

import { CouponField } from "@/components/cart/CouponField";
import { FreeShippingProgress } from "@/components/cart/FreeShippingProgress";
import { EmptyState } from "@/components/ui/EmptyState";
import { useIsAuthenticated } from "@/hooks/useAuth";
import { useUnifiedCart } from "@/hooks/useUnifiedCart";

function formatUSD(value: number): string {
  return value.toLocaleString("en-US", { style: "currency", currency: "USD" });
}

export function CartPage() {
  const cart = useUnifiedCart();
  const isAuthenticated = useIsAuthenticated();
  const navigate = useNavigate();

  return (
    <div className="container-veloura py-10">
      <h1 className="font-display text-3xl text-ink">Your Bag</h1>

      {cart.isLoading ? (
        <div className="mt-8 space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="skeleton h-32 w-full rounded-lg" />
          ))}
        </div>
      ) : cart.items.length === 0 ? (
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
                <Link to={`/products/${item.slug}`} className="shrink-0">
                  <img src={item.image} alt={item.name} className="h-32 w-24 rounded object-cover" />
                </Link>
                <div className="flex flex-1 flex-col gap-1.5">
                  <span className="text-xs uppercase tracking-wider text-ink-secondary">{item.brand}</span>
                  <Link to={`/products/${item.slug}`} className="font-medium text-ink hover:text-burgundy">
                    {item.name}
                  </Link>
                  <span className="text-sm text-ink-secondary">
                    {item.color} · Size {item.size}
                  </span>
                  <div className="mt-2 flex items-center justify-between">
                    <div className="flex items-center rounded border border-border">
                      <button
                        aria-label="Decrease quantity"
                        className="flex h-9 w-9 items-center justify-center disabled:opacity-30"
                        disabled={item.quantity <= 1}
                        onClick={() => cart.updateQuantity(item.id, item.quantity - 1)}
                      >
                        <Minus className="h-3.5 w-3.5" />
                      </button>
                      <span className="w-8 text-center text-sm tabular-nums">{item.quantity}</span>
                      <button
                        aria-label="Increase quantity"
                        className="flex h-9 w-9 items-center justify-center disabled:opacity-30"
                        disabled={item.quantity >= item.inventoryQuantity}
                        onClick={() => cart.updateQuantity(item.id, item.quantity + 1)}
                      >
                        <Plus className="h-3.5 w-3.5" />
                      </button>
                    </div>
                    <span className="font-medium text-ink">{formatUSD(item.lineTotal)}</span>
                  </div>
                  {cart.canMoveToWishlist && (
                    <div className="mt-1 flex items-center gap-4">
                      <button
                        onClick={() => cart.moveToWishlist(item.id)}
                        className="flex items-center gap-1 text-xs text-ink-secondary hover:text-burgundy"
                      >
                        <Heart className="h-3.5 w-3.5" /> Move to Wishlist
                      </button>
                    </div>
                  )}
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

          <div className="h-fit rounded-lg border border-border bg-surface p-6">
            <h2 className="font-display text-xl text-ink">Order Summary</h2>

            <div className="mt-4">
              <FreeShippingProgress remaining={cart.freeShippingRemaining} subtotal={cart.subtotal} />
            </div>

            <div className="mt-4 space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-ink-secondary">Subtotal</span>
                <span className="font-medium text-ink">{formatUSD(cart.subtotal)}</span>
              </div>
              {cart.discountAmount > 0 && (
                <div className="flex justify-between text-burgundy">
                  <span>Discount</span>
                  <span>-{formatUSD(cart.discountAmount)}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-ink-secondary">Estimated shipping</span>
                <span className="text-ink">{cart.shippingEstimate === 0 ? "Free" : formatUSD(cart.shippingEstimate)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-ink-secondary">Estimated tax</span>
                <span className="text-ink">{formatUSD(cart.taxEstimate)}</span>
              </div>
              <div className="flex justify-between border-t border-border pt-2 text-base font-semibold">
                <span className="text-ink">Estimated Total</span>
                <span className="text-ink">{formatUSD(cart.estimatedTotal)}</span>
              </div>
            </div>

            {cart.canApplyCoupon ? (
              <div className="mt-4">
                <CouponField couponCode={cart.couponCode} couponError={cart.couponError} />
              </div>
            ) : (
              <p className="mt-4 text-xs text-ink-secondary">Sign in at checkout to apply a coupon code.</p>
            )}

            <button
              onClick={() => (isAuthenticated ? navigate("/checkout") : navigate("/login", { state: { from: "/checkout" } }))}
              className="btn-primary mt-5 w-full"
            >
              Proceed to Checkout
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

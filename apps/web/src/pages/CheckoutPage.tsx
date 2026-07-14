import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useCart } from "@/hooks/useCart";
import { useCreateOrder } from "@/hooks/useOrders";
import { getApiErrorMessage } from "@/services/apiClient";
import { type ShippingAddressFormValues, shippingAddressSchema } from "@/schemas/checkout";
import { useToastStore } from "@/store/toastStore";

const FREE_SHIPPING_THRESHOLD = 100;
const STANDARD_SHIPPING = 7.99;
const TAX_RATE = 0.0825;

function formatUSD(value: number): string {
  return value.toLocaleString("en-US", { style: "currency", currency: "USD" });
}

export function CheckoutPage() {
  const { data: cart, isLoading } = useCart();
  const createOrder = useCreateOrder();
  const navigate = useNavigate();
  const push = useToastStore((s) => s.push);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ShippingAddressFormValues>({
    resolver: zodResolver(shippingAddressSchema),
    defaultValues: { country: "United States" },
  });

  useEffect(() => {
    if (!isLoading && cart && cart.items.length === 0) {
      navigate("/cart");
    }
  }, [isLoading, cart, navigate]);

  if (!cart) return null;

  const shipping = cart.subtotal >= FREE_SHIPPING_THRESHOLD ? 0 : STANDARD_SHIPPING;
  const tax = cart.subtotal * TAX_RATE;
  const total = cart.subtotal + shipping + tax;

  async function onSubmit(values: ShippingAddressFormValues) {
    try {
      const order = await createOrder.mutateAsync(values);
      navigate(`/order-success/${order.id}`);
    } catch (error) {
      push(getApiErrorMessage(error, "Checkout failed. Please check your cart and try again."), "error");
    }
  }

  return (
    <div className="container-veloura py-10">
      <h1 className="font-display text-3xl text-ink">Checkout</h1>

      <form onSubmit={handleSubmit(onSubmit)} className="mt-8 grid gap-10 lg:grid-cols-[1fr_380px]">
        <div className="flex flex-col gap-5 rounded-lg border border-border bg-surface p-6">
          <h2 className="font-display text-xl text-ink">Shipping Address</h2>
          <Input label="Full Name" {...register("full_name")} error={errors.full_name?.message} />
          <Input label="Address Line 1" {...register("line1")} error={errors.line1?.message} />
          <Input label="Address Line 2 (optional)" {...register("line2")} error={errors.line2?.message} />
          <div className="grid grid-cols-2 gap-4">
            <Input label="City" {...register("city")} error={errors.city?.message} />
            <Input label="State / Province" {...register("state")} error={errors.state?.message} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Input label="Postal Code" {...register("postal_code")} error={errors.postal_code?.message} />
            <Input label="Country" {...register("country")} error={errors.country?.message} />
          </div>
          <Input label="Phone" type="tel" {...register("phone")} error={errors.phone?.message} />

          <div className="mt-2 rounded border border-border bg-background px-4 py-3 text-xs text-ink-secondary">
            This is a simulated checkout for demo purposes — no real payment is collected.
          </div>
        </div>

        <div className="h-fit rounded-lg border border-border bg-surface p-6">
          <h2 className="font-display text-xl text-ink">Order Summary</h2>
          <div className="mt-4 divide-y divide-border">
            {cart.items.map((item) => (
              <div key={item.id} className="flex gap-3 py-3">
                <img src={item.variant.image_url} alt="" className="h-16 w-12 rounded object-cover" />
                <div className="flex-1 text-sm">
                  <p className="font-medium text-ink">{item.variant.product_name}</p>
                  <p className="text-xs text-ink-secondary">
                    {item.variant.color_name} · {item.variant.size} · Qty {item.quantity}
                  </p>
                </div>
                <span className="text-sm font-medium text-ink">{formatUSD(item.line_total)}</span>
              </div>
            ))}
          </div>
          <div className="mt-4 space-y-2 border-t border-border pt-4 text-sm">
            <div className="flex justify-between">
              <span className="text-ink-secondary">Subtotal</span>
              <span className="text-ink">{formatUSD(cart.subtotal)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-ink-secondary">Shipping</span>
              <span className="text-ink">{shipping === 0 ? "Free" : formatUSD(shipping)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-ink-secondary">Tax (8.25%)</span>
              <span className="text-ink">{formatUSD(tax)}</span>
            </div>
            <div className="flex justify-between border-t border-border pt-2 text-base font-semibold">
              <span className="text-ink">Total</span>
              <span className="text-ink">{formatUSD(total)}</span>
            </div>
          </div>
          <Button type="submit" size="lg" className="mt-5 w-full" isLoading={createOrder.isPending}>
            Place Order
          </Button>
          <Link to="/cart" className="mt-3 block text-center text-sm text-ink-secondary hover:text-ink">
            Back to bag
          </Link>
        </div>
      </form>
    </div>
  );
}

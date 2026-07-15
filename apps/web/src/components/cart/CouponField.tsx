import { Tag, X } from "lucide-react";
import { useState } from "react";

import { useApplyCoupon, useRemoveCoupon } from "@/hooks/useCart";

export function CouponField({
  couponCode,
  couponError,
}: {
  couponCode: string | null;
  couponError?: string | null;
}) {
  const [code, setCode] = useState("");
  const applyCoupon = useApplyCoupon();
  const removeCoupon = useRemoveCoupon();

  if (couponCode) {
    return (
      <div className="flex items-center justify-between rounded border border-border bg-background px-3 py-2 text-sm">
        <span className="flex items-center gap-1.5 font-medium text-ink">
          <Tag className="h-3.5 w-3.5" /> {couponCode}
        </span>
        <button
          onClick={() => removeCoupon.mutate()}
          aria-label="Remove coupon"
          className="text-ink-secondary hover:text-error"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    );
  }

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        if (code.trim()) applyCoupon.mutate(code.trim(), { onSuccess: () => setCode("") });
      }}
      className="flex flex-col gap-1.5"
    >
      <div className="flex gap-2">
        <input
          type="text"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="Coupon code"
          aria-label="Coupon code"
          className="input-veloura flex-1 uppercase placeholder:normal-case"
        />
        <button type="submit" disabled={applyCoupon.isPending || !code.trim()} className="btn-secondary shrink-0 disabled:opacity-50">
          Apply
        </button>
      </div>
      {couponError && <p className="text-xs text-error">{couponError}</p>}
    </form>
  );
}

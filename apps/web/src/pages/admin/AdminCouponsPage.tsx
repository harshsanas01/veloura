import { zodResolver } from "@hookform/resolvers/zod";
import { Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { AdminTable } from "@/components/admin/AdminTable";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { Select } from "@/components/ui/Select";
import {
  useAdminCoupons,
  useCreateAdminCoupon,
  useDeleteAdminCoupon,
  useUpdateAdminCoupon,
} from "@/hooks/useAdmin";
import type { AdminCoupon } from "@/types";

const couponSchema = z.object({
  code: z.string().min(1, "Code is required.").max(40),
  discount_type: z.enum(["fixed", "percentage"]),
  discount_value: z.coerce.number().min(0),
  free_shipping: z.boolean().optional().default(false),
  min_order_value: z.coerce.number().optional(),
  max_discount: z.coerce.number().optional(),
  usage_limit: z.coerce.number().optional(),
  per_user_limit: z.coerce.number().optional(),
});
type CouponFormValues = z.infer<typeof couponSchema>;

function formatUSD(value: number): string {
  return value.toLocaleString("en-US", { style: "currency", currency: "USD" });
}

export function AdminCouponsPage() {
  const { data: coupons, isLoading } = useAdminCoupons();
  const createCoupon = useCreateAdminCoupon();
  const updateCoupon = useUpdateAdminCoupon();
  const deleteCoupon = useDeleteAdminCoupon();
  const [isFormOpen, setFormOpen] = useState(false);
  const [deleting, setDeleting] = useState<AdminCoupon | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CouponFormValues>({
    resolver: zodResolver(couponSchema),
    defaultValues: { discount_type: "percentage", free_shipping: false },
  });

  async function onSubmit(values: CouponFormValues) {
    await createCoupon.mutateAsync(values, {
      onSuccess: () => {
        setFormOpen(false);
        reset();
      },
    });
  }

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-3xl text-ink">Coupons</h1>
          <p className="mt-1 text-sm text-ink-secondary">Manage promotional discount codes.</p>
        </div>
        <Button onClick={() => setFormOpen(true)}>
          <Plus className="h-4 w-4" /> Add Coupon
        </Button>
      </div>

      <div className="mt-6">
        {isLoading ? (
          <div className="skeleton h-64 w-full rounded-lg" />
        ) : (
          <AdminTable<AdminCoupon>
            rows={coupons ?? []}
            emptyMessage="No coupons yet."
            columns={[
              { header: "Code", render: (c) => <span className="font-medium">{c.code}</span> },
              {
                header: "Discount",
                render: (c) =>
                  c.discount_type === "percentage" ? `${c.discount_value}%` : formatUSD(c.discount_value),
              },
              { header: "Free Shipping", render: (c) => (c.free_shipping ? "Yes" : "No") },
              { header: "Min Order", render: (c) => (c.min_order_value ? formatUSD(c.min_order_value) : "—") },
              { header: "Redemptions", render: (c) => `${c.total_redemptions}${c.usage_limit ? ` / ${c.usage_limit}` : ""}` },
              {
                header: "Status",
                render: (c) => <Badge variant={c.is_active ? "success" : "neutral"}>{c.is_active ? "Active" : "Inactive"}</Badge>,
              },
              {
                header: "Actions",
                render: (c) => (
                  <div className="flex items-center gap-3">
                    <button
                      className="text-xs font-medium text-ink-secondary hover:text-ink"
                      onClick={() => updateCoupon.mutate({ id: c.id, payload: { is_active: !c.is_active } })}
                    >
                      {c.is_active ? "Deactivate" : "Activate"}
                    </button>
                    <button
                      aria-label="Delete coupon"
                      className="text-ink-secondary hover:text-error"
                      onClick={() => setDeleting(c)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ),
              },
            ]}
          />
        )}
      </div>

      <Modal isOpen={isFormOpen} onClose={() => setFormOpen(false)} title="Add Coupon">
        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-3">
          <Input label="Code" {...register("code")} error={errors.code?.message} />
          <Select label="Discount Type" {...register("discount_type")}>
            <option value="percentage">Percentage</option>
            <option value="fixed">Fixed Amount</option>
          </Select>
          <Input
            label="Discount Value"
            type="number"
            step="0.01"
            {...register("discount_value")}
            error={errors.discount_value?.message}
          />
          <div className="grid grid-cols-2 gap-3">
            <Input label="Min Order Value (optional)" type="number" step="0.01" {...register("min_order_value")} />
            <Input label="Max Discount (optional)" type="number" step="0.01" {...register("max_discount")} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Input label="Usage Limit (optional)" type="number" {...register("usage_limit")} />
            <Input label="Per-User Limit (optional)" type="number" {...register("per_user_limit")} />
          </div>
          <label className="flex items-center gap-2 text-sm text-ink">
            <input type="checkbox" className="h-4 w-4 accent-burgundy" {...register("free_shipping")} />
            Grants free shipping
          </label>
          <Button type="submit" isLoading={createCoupon.isPending} className="mt-2">
            Create Coupon
          </Button>
        </form>
      </Modal>

      <ConfirmDialog
        isOpen={Boolean(deleting)}
        onClose={() => setDeleting(null)}
        onConfirm={() => deleting && deleteCoupon.mutate(deleting.id, { onSuccess: () => setDeleting(null) })}
        title="Delete coupon?"
        description={`This permanently deletes the coupon "${deleting?.code}". Past redemptions are kept for order history.`}
        confirmLabel="Delete Coupon"
        isLoading={deleteCoupon.isPending}
      />
    </div>
  );
}

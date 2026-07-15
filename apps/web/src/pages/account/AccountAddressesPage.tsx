import { zodResolver } from "@hookform/resolvers/zod";
import { MapPin, Pencil, Trash2 } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { useAddressMutations, useAddresses } from "@/hooks/useAccount";
import type { Address } from "@/types";

const addressSchema = z.object({
  full_name: z.string().min(1, "Full name is required."),
  line1: z.string().min(1, "Address line 1 is required."),
  line2: z.string().optional().default(""),
  city: z.string().min(1, "City is required."),
  state: z.string().min(1, "State is required."),
  postal_code: z.string().min(1, "Postal code is required."),
  country: z.string().min(1, "Country is required."),
  phone: z.string().min(1, "Phone is required."),
  is_default_shipping: z.boolean().optional().default(false),
  is_default_billing: z.boolean().optional().default(false),
});
type AddressFormValues = z.infer<typeof addressSchema>;

export function AccountAddressesPage() {
  const { data: addresses, isLoading } = useAddresses();
  const { create, update, remove } = useAddressMutations();
  const [modalAddress, setModalAddress] = useState<Address | "new" | null>(null);

  const form = useForm<AddressFormValues>({
    resolver: zodResolver(addressSchema),
    defaultValues: {
      full_name: "",
      line1: "",
      line2: "",
      city: "",
      state: "",
      postal_code: "",
      country: "United States",
      phone: "",
      is_default_shipping: false,
      is_default_billing: false,
    },
  });

  function openNew() {
    form.reset({
      full_name: "",
      line1: "",
      line2: "",
      city: "",
      state: "",
      postal_code: "",
      country: "United States",
      phone: "",
      is_default_shipping: false,
      is_default_billing: false,
    });
    setModalAddress("new");
  }

  function openEdit(address: Address) {
    form.reset({ ...address, line2: address.line2 ?? "" });
    setModalAddress(address);
  }

  async function onSubmit(values: AddressFormValues) {
    if (modalAddress === "new") {
      await create.mutateAsync(values, { onSuccess: () => setModalAddress(null) });
    } else if (modalAddress) {
      await update.mutateAsync(
        { id: modalAddress.id, payload: values },
        { onSuccess: () => setModalAddress(null) },
      );
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2].map((i) => (
          <div key={i} className="skeleton h-32 w-full rounded-lg" />
        ))}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h2 className="font-display text-xl text-ink">Saved Addresses</h2>
        <Button size="sm" onClick={openNew}>
          Add Address
        </Button>
      </div>

      {!addresses || addresses.length === 0 ? (
        <EmptyState
          icon={MapPin}
          title="No saved addresses"
          description="Add an address to speed up checkout next time."
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {addresses.map((address) => (
            <div key={address.id} className="rounded-lg border border-border bg-surface p-5">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="font-medium text-ink">{address.full_name}</p>
                  <p className="mt-1 text-sm text-ink-secondary">
                    {address.line1}
                    {address.line2 ? `, ${address.line2}` : ""}
                    <br />
                    {address.city}, {address.state} {address.postal_code}
                    <br />
                    {address.country}
                    <br />
                    {address.phone}
                  </p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {address.is_default_shipping && (
                      <span className="rounded-full bg-rose/40 px-2.5 py-1 text-xs font-medium text-burgundy">
                        Default Shipping
                      </span>
                    )}
                    {address.is_default_billing && (
                      <span className="rounded-full bg-rose/40 px-2.5 py-1 text-xs font-medium text-burgundy">
                        Default Billing
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex shrink-0 gap-1">
                  <button
                    aria-label="Edit address"
                    onClick={() => openEdit(address)}
                    className="rounded p-1.5 text-ink-secondary hover:bg-black/5 hover:text-ink"
                  >
                    <Pencil className="h-4 w-4" />
                  </button>
                  <button
                    aria-label="Delete address"
                    onClick={() => remove.mutate(address.id)}
                    className="rounded p-1.5 text-ink-secondary hover:bg-black/5 hover:text-error"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <Modal
        isOpen={modalAddress !== null}
        onClose={() => setModalAddress(null)}
        title={modalAddress === "new" ? "Add Address" : "Edit Address"}
      >
        <form onSubmit={form.handleSubmit(onSubmit)} className="flex flex-col gap-3">
          <Input label="Full Name" {...form.register("full_name")} error={form.formState.errors.full_name?.message} />
          <Input label="Address Line 1" {...form.register("line1")} error={form.formState.errors.line1?.message} />
          <Input label="Address Line 2 (optional)" {...form.register("line2")} />
          <div className="grid grid-cols-2 gap-3">
            <Input label="City" {...form.register("city")} error={form.formState.errors.city?.message} />
            <Input label="State" {...form.register("state")} error={form.formState.errors.state?.message} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Input label="Postal Code" {...form.register("postal_code")} error={form.formState.errors.postal_code?.message} />
            <Input label="Country" {...form.register("country")} error={form.formState.errors.country?.message} />
          </div>
          <Input label="Phone" {...form.register("phone")} error={form.formState.errors.phone?.message} />
          <label className="flex items-center gap-2 text-sm text-ink">
            <input type="checkbox" className="h-4 w-4 accent-burgundy" {...form.register("is_default_shipping")} />
            Set as default shipping address
          </label>
          <label className="flex items-center gap-2 text-sm text-ink">
            <input type="checkbox" className="h-4 w-4 accent-burgundy" {...form.register("is_default_billing")} />
            Set as default billing address
          </label>
          <Button type="submit" isLoading={create.isPending || update.isPending} className="mt-2 self-start">
            Save Address
          </Button>
        </form>
      </Modal>
    </div>
  );
}

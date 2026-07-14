import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { Select } from "@/components/ui/Select";
import { useCategories } from "@/hooks/useProducts";
import type { AdminProductInput, AdminVariantInput } from "@/services/adminApi";
import type { Gender } from "@/types";

interface ProductFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (payload: AdminProductInput) => void;
  isSubmitting?: boolean;
}

const emptyVariant: AdminVariantInput = {
  sku: "",
  size: "M",
  color_name: "Black",
  color_hex: "#111111",
  inventory_quantity: 10,
  image_url: "https://images.unsplash.com/photo-1445205170230-053b83016050?w=900&q=80",
};

export function ProductFormModal({ isOpen, onClose, onSubmit, isSubmitting }: ProductFormModalProps) {
  const { data: categories } = useCategories();
  const [form, setForm] = useState<Omit<AdminProductInput, "variants" | "occasion_tags" | "style_tags" | "season_tags">>({
    name: "",
    brand: "",
    description: "",
    short_description: "",
    gender: "unisex" as Gender,
    category_id: "",
    base_price: 0,
    sale_price: null,
    material: "",
    care_instructions: "Machine wash cold, tumble dry low.",
    is_featured: false,
    is_active: true,
  });
  const [tags, setTags] = useState({ occasion: "", style: "", season: "" });
  const [variants, setVariants] = useState<AdminVariantInput[]>([{ ...emptyVariant }]);

  function updateVariant(index: number, patch: Partial<AdminVariantInput>) {
    setVariants((prev) => prev.map((v, i) => (i === index ? { ...v, ...patch } : v)));
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    onSubmit({
      ...form,
      category_id: form.category_id || categories?.[0]?.id || "",
      occasion_tags: tags.occasion.split(",").map((t) => t.trim()).filter(Boolean),
      style_tags: tags.style.split(",").map((t) => t.trim()).filter(Boolean),
      season_tags: tags.season.split(",").map((t) => t.trim()).filter(Boolean),
      variants,
    });
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Add Product">
      <form onSubmit={handleSubmit} className="flex max-h-[70vh] flex-col gap-4 overflow-y-auto pr-1">
        <div className="grid grid-cols-2 gap-3">
          <Input label="Name" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <Input label="Brand" required value={form.brand} onChange={(e) => setForm({ ...form, brand: e.target.value })} />
        </div>
        <Input
          label="Short Description"
          required
          value={form.short_description}
          onChange={(e) => setForm({ ...form, short_description: e.target.value })}
        />
        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-medium text-ink">Description</label>
          <textarea
            required
            rows={3}
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            className="input-veloura"
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <Select label="Gender" value={form.gender} onChange={(e) => setForm({ ...form, gender: e.target.value as Gender })}>
            <option value="men">Men</option>
            <option value="women">Women</option>
            <option value="unisex">Unisex</option>
          </Select>
          <Select
            label="Category"
            value={form.category_id}
            onChange={(e) => setForm({ ...form, category_id: e.target.value })}
          >
            <option value="">Select category</option>
            {categories?.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </Select>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <Input
            label="Base Price"
            type="number"
            step="0.01"
            required
            value={form.base_price}
            onChange={(e) => setForm({ ...form, base_price: Number(e.target.value) })}
          />
          <Input
            label="Sale Price (optional)"
            type="number"
            step="0.01"
            value={form.sale_price ?? ""}
            onChange={(e) => setForm({ ...form, sale_price: e.target.value ? Number(e.target.value) : null })}
          />
        </div>
        <Input label="Material" required value={form.material} onChange={(e) => setForm({ ...form, material: e.target.value })} />

        <div className="grid grid-cols-3 gap-3">
          <Input label="Occasion tags (csv)" value={tags.occasion} onChange={(e) => setTags({ ...tags, occasion: e.target.value })} />
          <Input label="Style tags (csv)" value={tags.style} onChange={(e) => setTags({ ...tags, style: e.target.value })} />
          <Input label="Season tags (csv)" value={tags.season} onChange={(e) => setTags({ ...tags, season: e.target.value })} />
        </div>

        <div className="flex gap-6">
          <label className="flex items-center gap-2 text-sm text-ink">
            <input
              type="checkbox"
              checked={form.is_featured}
              onChange={(e) => setForm({ ...form, is_featured: e.target.checked })}
              className="h-4 w-4 accent-burgundy"
            />
            Featured
          </label>
          <label className="flex items-center gap-2 text-sm text-ink">
            <input
              type="checkbox"
              checked={form.is_active}
              onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
              className="h-4 w-4 accent-burgundy"
            />
            Active
          </label>
        </div>

        <div>
          <div className="mb-2 flex items-center justify-between">
            <span className="text-sm font-medium text-ink">Variants</span>
            <button
              type="button"
              onClick={() => setVariants((prev) => [...prev, { ...emptyVariant, sku: "" }])}
              className="text-xs font-medium text-burgundy hover:text-burgundy-hover"
            >
              + Add variant
            </button>
          </div>
          <div className="flex flex-col gap-2">
            {variants.map((variant, i) => (
              <div key={i} className="grid grid-cols-5 gap-2 rounded border border-border p-2">
                <Input placeholder="SKU" value={variant.sku} onChange={(e) => updateVariant(i, { sku: e.target.value })} />
                <Input placeholder="Size" value={variant.size} onChange={(e) => updateVariant(i, { size: e.target.value })} />
                <Input placeholder="Color" value={variant.color_name} onChange={(e) => updateVariant(i, { color_name: e.target.value })} />
                <Input type="color" value={variant.color_hex} onChange={(e) => updateVariant(i, { color_hex: e.target.value })} />
                <Input
                  type="number"
                  placeholder="Qty"
                  value={variant.inventory_quantity}
                  onChange={(e) => updateVariant(i, { inventory_quantity: Number(e.target.value) })}
                />
              </div>
            ))}
          </div>
        </div>

        <div className="flex justify-end gap-3 border-t border-border pt-4">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" isLoading={isSubmitting}>
            Create Product
          </Button>
        </div>
      </form>
    </Modal>
  );
}

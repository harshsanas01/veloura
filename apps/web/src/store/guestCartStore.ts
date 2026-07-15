import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface GuestCartItem {
  variantId: string;
  quantity: number;
  productSlug: string;
  productName: string;
  productBrand: string;
  imageUrl: string;
  colorName: string;
  size: string;
  unitPrice: number;
  inventoryQuantity: number;
}

interface GuestCartState {
  items: GuestCartItem[];
  addItem: (item: Omit<GuestCartItem, "quantity">, quantity: number) => void;
  updateQuantity: (variantId: string, quantity: number) => void;
  removeItem: (variantId: string) => void;
  clear: () => void;
}

export const useGuestCartStore = create<GuestCartState>()(
  persist(
    (set, get) => ({
      items: [],
      addItem: (item, quantity) => {
        const existing = get().items.find((i) => i.variantId === item.variantId);
        if (existing) {
          set({
            items: get().items.map((i) =>
              i.variantId === item.variantId
                ? { ...i, quantity: Math.min(i.quantity + quantity, item.inventoryQuantity) }
                : i,
            ),
          });
        } else {
          set({ items: [...get().items, { ...item, quantity }] });
        }
      },
      updateQuantity: (variantId, quantity) =>
        set({ items: get().items.map((i) => (i.variantId === variantId ? { ...i, quantity } : i)) }),
      removeItem: (variantId) => set({ items: get().items.filter((i) => i.variantId !== variantId) }),
      clear: () => set({ items: [] }),
    }),
    { name: "veloura_guest_cart" },
  ),
);

export function guestCartItemCount(): number {
  return useGuestCartStore.getState().items.reduce((sum, i) => sum + i.quantity, 0);
}

export function guestCartSubtotal(): number {
  return useGuestCartStore.getState().items.reduce((sum, i) => sum + i.unitPrice * i.quantity, 0);
}

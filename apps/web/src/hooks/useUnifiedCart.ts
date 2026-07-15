import { useMemo } from "react";

import {
  useCart,
  useMoveToWishlist,
  useRemoveCartItem,
  useUpdateCartItem,
} from "@/hooks/useCart";
import { useIsAuthenticated } from "@/hooks/useAuth";
import { useGuestCartStore } from "@/store/guestCartStore";

// Mirrors apps/api's services/pricing.py - used only for a guest-facing
// preview before login; the server always computes the authoritative totals
// once the guest cart is merged into a real account at login/checkout.
const FREE_SHIPPING_THRESHOLD = 100;
const STANDARD_SHIPPING = 7.99;
const TAX_RATE = 0.0825;

export interface UnifiedCartItem {
  id: string;
  slug: string;
  name: string;
  brand: string;
  image: string;
  color: string;
  size: string;
  quantity: number;
  unitPrice: number;
  lineTotal: number;
  inventoryQuantity: number;
}

export interface UnifiedCart {
  isGuest: boolean;
  isLoading: boolean;
  items: UnifiedCartItem[];
  subtotal: number;
  discountAmount: number;
  shippingEstimate: number;
  taxEstimate: number;
  estimatedTotal: number;
  freeShippingRemaining: number;
  couponCode: string | null;
  couponError: string | null;
  canApplyCoupon: boolean;
  canMoveToWishlist: boolean;
  updateQuantity: (id: string, quantity: number) => void;
  removeItem: (id: string) => void;
  moveToWishlist: (id: string) => void;
}

export function useUnifiedCart(): UnifiedCart {
  const isAuthenticated = useIsAuthenticated();
  const { data: cart, isLoading } = useCart();
  const updateItem = useUpdateCartItem();
  const removeCartItem = useRemoveCartItem();
  const moveToWishlistMutation = useMoveToWishlist();

  const guestItems = useGuestCartStore((s) => s.items);
  const updateGuestQuantity = useGuestCartStore((s) => s.updateQuantity);
  const removeGuestItem = useGuestCartStore((s) => s.removeItem);

  return useMemo(() => {
    if (isAuthenticated) {
      const items: UnifiedCartItem[] = (cart?.items ?? []).map((item) => ({
        id: item.id,
        slug: item.variant.product_slug,
        name: item.variant.product_name,
        brand: item.variant.product_brand,
        image: item.variant.image_url,
        color: item.variant.color_name,
        size: item.variant.size,
        quantity: item.quantity,
        unitPrice: item.variant.unit_price,
        lineTotal: item.line_total,
        inventoryQuantity: item.variant.inventory_quantity,
      }));
      return {
        isGuest: false,
        isLoading,
        items,
        subtotal: cart?.subtotal ?? 0,
        discountAmount: cart?.discount_amount ?? 0,
        shippingEstimate: cart?.shipping_estimate ?? 0,
        taxEstimate: cart?.tax_estimate ?? 0,
        estimatedTotal: cart?.estimated_total ?? 0,
        freeShippingRemaining: cart?.free_shipping_remaining ?? 0,
        couponCode: cart?.coupon_code ?? null,
        couponError: cart?.coupon_error ?? null,
        canApplyCoupon: true,
        canMoveToWishlist: true,
        updateQuantity: (id, quantity) => updateItem.mutate({ itemId: id, quantity }),
        removeItem: (id) => removeCartItem.mutate(id),
        moveToWishlist: (id) => moveToWishlistMutation.mutate(id),
      };
    }

    const items: UnifiedCartItem[] = guestItems.map((item) => ({
      id: item.variantId,
      slug: item.productSlug,
      name: item.productName,
      brand: item.productBrand,
      image: item.imageUrl,
      color: item.colorName,
      size: item.size,
      quantity: item.quantity,
      unitPrice: item.unitPrice,
      lineTotal: item.unitPrice * item.quantity,
      inventoryQuantity: item.inventoryQuantity,
    }));
    const subtotal = items.reduce((sum, i) => sum + i.lineTotal, 0);
    const shippingEstimate = subtotal >= FREE_SHIPPING_THRESHOLD || subtotal === 0 ? 0 : STANDARD_SHIPPING;
    const taxEstimate = subtotal * TAX_RATE;

    return {
      isGuest: true,
      isLoading: false,
      items,
      subtotal,
      discountAmount: 0,
      shippingEstimate,
      taxEstimate,
      estimatedTotal: subtotal + shippingEstimate + taxEstimate,
      freeShippingRemaining: Math.max(0, FREE_SHIPPING_THRESHOLD - subtotal),
      couponCode: null,
      couponError: null,
      canApplyCoupon: false,
      canMoveToWishlist: false,
      updateQuantity: (id, quantity) => updateGuestQuantity(id, quantity),
      removeItem: (id) => removeGuestItem(id),
      moveToWishlist: () => undefined,
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated, cart, isLoading, guestItems]);
}

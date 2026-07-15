import { apiClient } from "@/services/apiClient";
import type { Cart } from "@/types";

export const cartApi = {
  get: () => apiClient.get<Cart>("/cart").then((r) => r.data),

  addItem: (variant_id: string, quantity = 1) =>
    apiClient.post<Cart>("/cart/items", { variant_id, quantity }).then((r) => r.data),

  updateItem: (itemId: string, quantity: number) =>
    apiClient.patch<Cart>(`/cart/items/${itemId}`, { quantity }).then((r) => r.data),

  removeItem: (itemId: string) =>
    apiClient.delete<Cart>(`/cart/items/${itemId}`).then((r) => r.data),

  moveToWishlist: (itemId: string) =>
    apiClient.post<Cart>(`/cart/items/${itemId}/move-to-wishlist`).then((r) => r.data),

  applyCoupon: (code: string) => apiClient.post<Cart>("/cart/coupon", { code }).then((r) => r.data),

  removeCoupon: () => apiClient.delete<Cart>("/cart/coupon").then((r) => r.data),
};

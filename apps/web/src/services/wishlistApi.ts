import { apiClient } from "@/services/apiClient";
import type { Wishlist } from "@/types";

export const wishlistApi = {
  get: () => apiClient.get<Wishlist>("/wishlist").then((r) => r.data),

  addItem: (product_id: string) =>
    apiClient.post<Wishlist>("/wishlist/items", { product_id }).then((r) => r.data),

  removeItem: (productId: string) =>
    apiClient.delete<Wishlist>(`/wishlist/items/${productId}`).then((r) => r.data),
};

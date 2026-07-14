import { apiClient } from "@/services/apiClient";
import type { AdminOrder, AdminProduct, Gender, OrderStatus } from "@/types";

export interface AdminVariantInput {
  sku: string;
  size: string;
  color_name: string;
  color_hex: string;
  inventory_quantity: number;
  image_url: string;
}

export interface AdminProductInput {
  name: string;
  brand: string;
  description: string;
  short_description: string;
  gender: Gender;
  category_id: string;
  base_price: number;
  sale_price?: number | null;
  material: string;
  care_instructions: string;
  occasion_tags: string[];
  style_tags: string[];
  season_tags: string[];
  is_featured: boolean;
  is_active: boolean;
  variants: AdminVariantInput[];
}

export const adminApi = {
  listProducts: () => apiClient.get<AdminProduct[]>("/admin/products").then((r) => r.data),

  createProduct: (payload: AdminProductInput) =>
    apiClient.post<AdminProduct>("/admin/products", payload).then((r) => r.data),

  updateProduct: (id: string, payload: Partial<AdminProductInput>) =>
    apiClient.patch<AdminProduct>(`/admin/products/${id}`, payload).then((r) => r.data),

  deleteProduct: (id: string) => apiClient.delete(`/admin/products/${id}`),

  addVariant: (productId: string, payload: AdminVariantInput) =>
    apiClient
      .post<AdminProduct>(`/admin/products/${productId}/variants`, payload)
      .then((r) => r.data),

  updateVariant: (variantId: string, payload: Partial<AdminVariantInput>) =>
    apiClient.patch(`/admin/variants/${variantId}`, payload).then((r) => r.data),

  listOrders: () => apiClient.get<AdminOrder[]>("/admin/orders").then((r) => r.data),

  updateOrderStatus: (orderId: string, status: OrderStatus) =>
    apiClient
      .patch<AdminOrder>(`/admin/orders/${orderId}/status`, { status })
      .then((r) => r.data),
};

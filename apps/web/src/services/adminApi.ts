import { apiClient } from "@/services/apiClient";
import type {
  AdminCoupon,
  AdminCouponInput,
  AdminCustomerListResponse,
  AdminDashboard,
  AdminOrder,
  AdminOrderListResponse,
  AdminProduct,
  AdminProductListResponse,
  Gender,
  OrderStatus,
  Review,
} from "@/types";

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
  listProducts: (params: { q?: string; page?: number; page_size?: number } = {}) =>
    apiClient.get<AdminProductListResponse>("/admin/products", { params }).then((r) => r.data),

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

  deleteVariant: (variantId: string) => apiClient.delete(`/admin/variants/${variantId}`),

  adjustInventory: (variantId: string, delta: number, reason: string) =>
    apiClient
      .post(`/admin/variants/${variantId}/adjust-inventory`, { delta, reason })
      .then((r) => r.data),

  listOrders: (params: { q?: string; order_status?: string; page?: number; page_size?: number } = {}) =>
    apiClient.get<AdminOrderListResponse>("/admin/orders", { params }).then((r) => r.data),

  updateOrderStatus: (orderId: string, orderStatus: OrderStatus, note?: string) =>
    apiClient
      .patch<AdminOrder>(`/admin/orders/${orderId}/status`, { status: orderStatus, note })
      .then((r) => r.data),

  getDashboard: () => apiClient.get<AdminDashboard>("/admin/dashboard").then((r) => r.data),

  listCustomers: (params: { q?: string; page?: number; page_size?: number } = {}) =>
    apiClient.get<AdminCustomerListResponse>("/admin/customers", { params }).then((r) => r.data),

  listCoupons: () => apiClient.get<AdminCoupon[]>("/admin/coupons").then((r) => r.data),

  createCoupon: (payload: AdminCouponInput) =>
    apiClient.post<AdminCoupon>("/admin/coupons", payload).then((r) => r.data),

  updateCoupon: (id: string, payload: Partial<AdminCouponInput>) =>
    apiClient.patch<AdminCoupon>(`/admin/coupons/${id}`, payload).then((r) => r.data),

  deleteCoupon: (id: string) => apiClient.delete(`/admin/coupons/${id}`),

  listAllReviews: () => apiClient.get<Review[]>("/admin/reviews").then((r) => r.data),

  moderateReview: (id: string, isActive: boolean) =>
    apiClient.patch<Review>(`/admin/reviews/${id}`, { is_active: isActive }).then((r) => r.data),
};

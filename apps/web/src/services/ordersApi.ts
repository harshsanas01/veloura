import { apiClient } from "@/services/apiClient";
import type { Order, OrderSummary, ShippingAddressInput } from "@/types";

export const ordersApi = {
  create: (payload: {
    shipping_address: ShippingAddressInput;
    coupon_code?: string | null;
    customer_notes?: string;
  }) => apiClient.post<Order>("/orders", payload).then((r) => r.data),

  list: () => apiClient.get<OrderSummary[]>("/orders").then((r) => r.data),

  getById: (orderId: string) => apiClient.get<Order>(`/orders/${orderId}`).then((r) => r.data),

  cancel: (orderId: string) => apiClient.post<Order>(`/orders/${orderId}/cancel`).then((r) => r.data),
};

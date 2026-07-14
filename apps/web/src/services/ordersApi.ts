import { apiClient } from "@/services/apiClient";
import type { Order, OrderSummary, ShippingAddressInput } from "@/types";

export const ordersApi = {
  create: (shipping_address: ShippingAddressInput) =>
    apiClient.post<Order>("/orders", { shipping_address }).then((r) => r.data),

  list: () => apiClient.get<OrderSummary[]>("/orders").then((r) => r.data),

  getById: (orderId: string) => apiClient.get<Order>(`/orders/${orderId}`).then((r) => r.data),
};

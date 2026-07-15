import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getApiErrorMessage } from "@/services/apiClient";
import { ordersApi } from "@/services/ordersApi";
import { useToastStore } from "@/store/toastStore";
import type { ShippingAddressInput } from "@/types";

export function useOrders() {
  return useQuery({
    queryKey: ["orders"],
    queryFn: ordersApi.list,
  });
}

export function useOrder(orderId: string | undefined) {
  return useQuery({
    queryKey: ["order", orderId],
    queryFn: () => ordersApi.getById(orderId as string),
    enabled: Boolean(orderId),
  });
}

export function useCreateOrder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: {
      shipping_address: ShippingAddressInput;
      coupon_code?: string | null;
      customer_notes?: string;
    }) => ordersApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cart"] });
      queryClient.invalidateQueries({ queryKey: ["orders"] });
    },
  });
}

export function useCancelOrder() {
  const queryClient = useQueryClient();
  const push = useToastStore((s) => s.push);
  return useMutation({
    mutationFn: (orderId: string) => ordersApi.cancel(orderId),
    onSuccess: (order) => {
      queryClient.setQueryData(["order", order.id], order);
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      push("Order cancelled.", "info");
    },
    onError: (error) => push(getApiErrorMessage(error, "Could not cancel this order."), "error"),
  });
}

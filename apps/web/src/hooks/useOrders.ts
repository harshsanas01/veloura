import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ordersApi } from "@/services/ordersApi";
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
    mutationFn: (address: ShippingAddressInput) => ordersApi.create(address),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cart"] });
      queryClient.invalidateQueries({ queryKey: ["orders"] });
    },
  });
}

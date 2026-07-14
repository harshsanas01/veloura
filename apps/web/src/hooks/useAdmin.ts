import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { adminApi, type AdminProductInput, type AdminVariantInput } from "@/services/adminApi";
import { getApiErrorMessage } from "@/services/apiClient";
import { useToastStore } from "@/store/toastStore";
import type { OrderStatus } from "@/types";

export function useAdminProducts() {
  return useQuery({ queryKey: ["admin-products"], queryFn: adminApi.listProducts });
}

export function useAdminOrders() {
  return useQuery({ queryKey: ["admin-orders"], queryFn: adminApi.listOrders });
}

export function useCreateAdminProduct() {
  const queryClient = useQueryClient();
  const push = useToastStore((s) => s.push);
  return useMutation({
    mutationFn: (payload: AdminProductInput) => adminApi.createProduct(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-products"] });
      queryClient.invalidateQueries({ queryKey: ["products"] });
      push("Product created.", "success");
    },
    onError: (error) => push(getApiErrorMessage(error), "error"),
  });
}

export function useUpdateAdminProduct() {
  const queryClient = useQueryClient();
  const push = useToastStore((s) => s.push);
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<AdminProductInput> }) =>
      adminApi.updateProduct(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-products"] });
      queryClient.invalidateQueries({ queryKey: ["products"] });
      push("Product updated.", "success");
    },
    onError: (error) => push(getApiErrorMessage(error), "error"),
  });
}

export function useDeleteAdminProduct() {
  const queryClient = useQueryClient();
  const push = useToastStore((s) => s.push);
  return useMutation({
    mutationFn: (id: string) => adminApi.deleteProduct(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-products"] });
      queryClient.invalidateQueries({ queryKey: ["products"] });
      push("Product deleted.", "success");
    },
    onError: (error) => push(getApiErrorMessage(error), "error"),
  });
}

export function useAddAdminVariant() {
  const queryClient = useQueryClient();
  const push = useToastStore((s) => s.push);
  return useMutation({
    mutationFn: ({ productId, payload }: { productId: string; payload: AdminVariantInput }) =>
      adminApi.addVariant(productId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-products"] });
      push("Variant added.", "success");
    },
    onError: (error) => push(getApiErrorMessage(error), "error"),
  });
}

export function useUpdateAdminVariant() {
  const queryClient = useQueryClient();
  const push = useToastStore((s) => s.push);
  return useMutation({
    mutationFn: ({
      variantId,
      payload,
    }: {
      variantId: string;
      payload: Partial<AdminVariantInput>;
    }) => adminApi.updateVariant(variantId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-products"] });
      push("Inventory updated.", "success");
    },
    onError: (error) => push(getApiErrorMessage(error), "error"),
  });
}

export function useUpdateAdminOrderStatus() {
  const queryClient = useQueryClient();
  const push = useToastStore((s) => s.push);
  return useMutation({
    mutationFn: ({ orderId, status }: { orderId: string; status: OrderStatus }) =>
      adminApi.updateOrderStatus(orderId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-orders"] });
      push("Order status updated.", "success");
    },
    onError: (error) => push(getApiErrorMessage(error), "error"),
  });
}

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { adminApi, type AdminProductInput, type AdminVariantInput } from "@/services/adminApi";
import { getApiErrorMessage } from "@/services/apiClient";
import { useToastStore } from "@/store/toastStore";
import type { AdminCouponInput, OrderStatus } from "@/types";

export function useAdminProducts(params: { q?: string; page?: number; page_size?: number } = {}) {
  return useQuery({
    queryKey: ["admin-products", params],
    queryFn: () => adminApi.listProducts(params),
    placeholderData: (prev) => prev,
  });
}

export function useAdminOrders(
  params: { q?: string; order_status?: string; page?: number; page_size?: number } = {},
) {
  return useQuery({
    queryKey: ["admin-orders", params],
    queryFn: () => adminApi.listOrders(params),
    placeholderData: (prev) => prev,
  });
}

export function useAdminDashboard() {
  return useQuery({ queryKey: ["admin-dashboard"], queryFn: adminApi.getDashboard });
}

export function useAdminCustomers(params: { q?: string; page?: number; page_size?: number } = {}) {
  return useQuery({
    queryKey: ["admin-customers", params],
    queryFn: () => adminApi.listCustomers(params),
    placeholderData: (prev) => prev,
  });
}

export function useAdminCoupons() {
  return useQuery({ queryKey: ["admin-coupons"], queryFn: adminApi.listCoupons });
}

export function useCreateAdminCoupon() {
  const queryClient = useQueryClient();
  const push = useToastStore((s) => s.push);
  return useMutation({
    mutationFn: (payload: AdminCouponInput) => adminApi.createCoupon(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-coupons"] });
      push("Coupon created.", "success");
    },
    onError: (error) => push(getApiErrorMessage(error), "error"),
  });
}

export function useUpdateAdminCoupon() {
  const queryClient = useQueryClient();
  const push = useToastStore((s) => s.push);
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<AdminCouponInput> }) =>
      adminApi.updateCoupon(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-coupons"] });
      push("Coupon updated.", "success");
    },
    onError: (error) => push(getApiErrorMessage(error), "error"),
  });
}

export function useDeleteAdminCoupon() {
  const queryClient = useQueryClient();
  const push = useToastStore((s) => s.push);
  return useMutation({
    mutationFn: (id: string) => adminApi.deleteCoupon(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-coupons"] });
      push("Coupon deleted.", "info");
    },
    onError: (error) => push(getApiErrorMessage(error), "error"),
  });
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

export function useDeleteAdminVariant() {
  const queryClient = useQueryClient();
  const push = useToastStore((s) => s.push);
  return useMutation({
    mutationFn: (variantId: string) => adminApi.deleteVariant(variantId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-products"] });
      push("Variant deleted.", "info");
    },
    onError: (error) => push(getApiErrorMessage(error), "error"),
  });
}

export function useAdjustInventory() {
  const queryClient = useQueryClient();
  const push = useToastStore((s) => s.push);
  return useMutation({
    mutationFn: ({ variantId, delta, reason }: { variantId: string; delta: number; reason: string }) =>
      adminApi.adjustInventory(variantId, delta, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-products"] });
      push("Inventory adjusted.", "success");
    },
    onError: (error) => push(getApiErrorMessage(error, "Could not adjust inventory."), "error"),
  });
}

export function useAdminReviews() {
  return useQuery({ queryKey: ["admin-reviews"], queryFn: adminApi.listAllReviews });
}

export function useModerateReview() {
  const queryClient = useQueryClient();
  const push = useToastStore((s) => s.push);
  return useMutation({
    mutationFn: ({ id, isActive }: { id: string; isActive: boolean }) =>
      adminApi.moderateReview(id, isActive),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-reviews"] });
      push("Review updated.", "success");
    },
    onError: (error) => push(getApiErrorMessage(error), "error"),
  });
}

export function useUpdateAdminOrderStatus() {
  const queryClient = useQueryClient();
  const push = useToastStore((s) => s.push);
  return useMutation({
    mutationFn: ({ orderId, status, note }: { orderId: string; status: OrderStatus; note?: string }) =>
      adminApi.updateOrderStatus(orderId, status, note),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-orders"] });
      queryClient.invalidateQueries({ queryKey: ["admin-dashboard"] });
      push("Order status updated.", "success");
    },
    onError: (error) => push(getApiErrorMessage(error), "error"),
  });
}

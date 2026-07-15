import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getApiErrorMessage } from "@/services/apiClient";
import { cartApi } from "@/services/cartApi";
import { useAuthStore } from "@/store/authStore";
import { useToastStore } from "@/store/toastStore";
import { useUIStore } from "@/store/uiStore";

export function useCart() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  return useQuery({
    queryKey: ["cart"],
    queryFn: cartApi.get,
    enabled: isAuthenticated,
  });
}

export function useAddToCart() {
  const queryClient = useQueryClient();
  const push = useToastStore((s) => s.push);
  const openCart = useUIStore((s) => s.openCart);

  return useMutation({
    mutationFn: ({ variantId, quantity }: { variantId: string; quantity?: number }) =>
      cartApi.addItem(variantId, quantity),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cart"] });
      push("Added to cart.", "success");
      openCart();
    },
    onError: (error) => push(getApiErrorMessage(error, "Could not add item to cart."), "error"),
  });
}

export function useUpdateCartItem() {
  const queryClient = useQueryClient();
  const push = useToastStore((s) => s.push);

  return useMutation({
    mutationFn: ({ itemId, quantity }: { itemId: string; quantity: number }) =>
      cartApi.updateItem(itemId, quantity),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["cart"] }),
    onError: (error) => push(getApiErrorMessage(error, "Could not update quantity."), "error"),
  });
}

export function useRemoveCartItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (itemId: string) => cartApi.removeItem(itemId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["cart"] }),
  });
}

export function useMoveToWishlist() {
  const queryClient = useQueryClient();
  const push = useToastStore((s) => s.push);
  return useMutation({
    mutationFn: (itemId: string) => cartApi.moveToWishlist(itemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cart"] });
      queryClient.invalidateQueries({ queryKey: ["wishlist"] });
      push("Moved to wishlist.", "success");
    },
    onError: (error) => push(getApiErrorMessage(error), "error"),
  });
}

export function useApplyCoupon() {
  const queryClient = useQueryClient();
  const push = useToastStore((s) => s.push);
  return useMutation({
    mutationFn: (code: string) => cartApi.applyCoupon(code),
    onSuccess: (cart) => {
      queryClient.setQueryData(["cart"], cart);
      push(`Coupon applied — $${cart.discount_amount.toFixed(2)} off.`, "success");
    },
    onError: (error) => push(getApiErrorMessage(error, "This coupon code isn't valid."), "error"),
  });
}

export function useRemoveCoupon() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => cartApi.removeCoupon(),
    onSuccess: (cart) => queryClient.setQueryData(["cart"], cart),
  });
}

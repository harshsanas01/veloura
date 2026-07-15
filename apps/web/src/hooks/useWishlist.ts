import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getApiErrorMessage } from "@/services/apiClient";
import { wishlistApi } from "@/services/wishlistApi";
import { useAuthStore } from "@/store/authStore";
import { useToastStore } from "@/store/toastStore";

export function useWishlist() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  return useQuery({
    queryKey: ["wishlist"],
    queryFn: wishlistApi.get,
    enabled: isAuthenticated,
  });
}

export function useToggleWishlist() {
  const queryClient = useQueryClient();
  const push = useToastStore((s) => s.push);

  const add = useMutation({
    mutationFn: (productId: string) => wishlistApi.addItem(productId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wishlist"] });
      push("Saved to wishlist.", "success");
    },
    onError: (error) => push(getApiErrorMessage(error), "error"),
  });

  const remove = useMutation({
    mutationFn: (productId: string) => wishlistApi.removeItem(productId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wishlist"] });
      push("Removed from wishlist.", "info");
    },
  });

  return { add, remove };
}

export function useMoveWishlistItemToCart() {
  const queryClient = useQueryClient();
  const push = useToastStore((s) => s.push);

  return useMutation({
    mutationFn: ({ productId, variantId, quantity }: { productId: string; variantId: string; quantity?: number }) =>
      wishlistApi.moveToCart(productId, variantId, quantity),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["wishlist"] });
      queryClient.invalidateQueries({ queryKey: ["cart"] });
      push("Moved to your bag.", "success");
    },
    onError: (error) => push(getApiErrorMessage(error, "Could not move this item to your bag."), "error"),
  });
}

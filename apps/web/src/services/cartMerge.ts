import type { QueryClient } from "@tanstack/react-query";

import { cartApi } from "@/services/cartApi";
import { useGuestCartStore } from "@/store/guestCartStore";
import { useToastStore } from "@/store/toastStore";

/** Merges the locally-stored guest cart into the now-authenticated user's real
 * cart, one item at a time so a single out-of-stock/removed item doesn't fail
 * the whole merge. Always clears the guest cart afterwards. */
export async function mergeGuestCartIntoAccount(queryClient: QueryClient): Promise<void> {
  const items = useGuestCartStore.getState().items;
  if (items.length === 0) return;

  let failures = 0;
  for (const item of items) {
    try {
      await cartApi.addItem(item.variantId, item.quantity);
    } catch {
      failures += 1;
    }
  }

  useGuestCartStore.getState().clear();
  await queryClient.invalidateQueries({ queryKey: ["cart"] });

  const push = useToastStore.getState().push;
  if (failures > 0) {
    push(
      failures === items.length
        ? "We couldn't restore your saved cart items - they may be out of stock."
        : `Restored your cart - ${failures} item(s) were no longer available.`,
      "info",
    );
  }
}

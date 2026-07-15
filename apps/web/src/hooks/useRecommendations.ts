import { useQuery } from "@tanstack/react-query";

import { recommendationsApi } from "@/services/recommendationsApi";
import type { Gender } from "@/types";

export function useTrending(gender?: Gender, limit = 8) {
  return useQuery({
    queryKey: ["trending", gender, limit],
    queryFn: () => recommendationsApi.trending(gender, limit),
  });
}

export function useAlsoBought(productId: string | undefined, limit = 4) {
  return useQuery({
    queryKey: ["also-bought", productId, limit],
    queryFn: () => recommendationsApi.alsoBought(productId as string, limit),
    enabled: Boolean(productId),
  });
}

export function useCompleteTheLook(productId: string | undefined, limit = 4) {
  return useQuery({
    queryKey: ["complete-the-look", productId, limit],
    queryFn: () => recommendationsApi.completeTheLook(productId as string, limit),
    enabled: Boolean(productId),
  });
}

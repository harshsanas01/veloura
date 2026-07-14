import { useQuery } from "@tanstack/react-query";

import { categoriesApi } from "@/services/categoriesApi";
import { productsApi } from "@/services/productsApi";
import type { ProductFilters } from "@/types";

export function useProducts(filters: ProductFilters) {
  return useQuery({
    queryKey: ["products", filters],
    queryFn: () => productsApi.list(filters),
    placeholderData: (prev) => prev,
  });
}

export function useProduct(slug: string | undefined) {
  return useQuery({
    queryKey: ["product", slug],
    queryFn: () => productsApi.getBySlug(slug as string),
    enabled: Boolean(slug),
  });
}

export function useRelatedProducts(productId: string | undefined) {
  return useQuery({
    queryKey: ["related-products", productId],
    queryFn: () => productsApi.getRelated(productId as string),
    enabled: Boolean(productId),
  });
}

export function useCategories() {
  return useQuery({
    queryKey: ["categories"],
    queryFn: categoriesApi.list,
    staleTime: 5 * 60 * 1000,
  });
}

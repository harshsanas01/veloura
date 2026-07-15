import { useQueries, useQuery } from "@tanstack/react-query";

import { categoriesApi } from "@/services/categoriesApi";
import { productsApi } from "@/services/productsApi";
import type { ProductFilters, ProductListItem } from "@/types";

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

export function useFacets() {
  return useQuery({
    queryKey: ["product-facets"],
    queryFn: productsApi.getFacets,
    staleTime: 5 * 60 * 1000,
  });
}

export function useProductsBySlug(slugs: string[]): { items: ProductListItem[]; isLoading: boolean } {
  const results = useQueries({
    queries: slugs.map((slug) => ({
      queryKey: ["product", slug],
      queryFn: () => productsApi.getBySlug(slug),
      staleTime: 60 * 1000,
    })),
  });

  const items: ProductListItem[] = results
    .filter((r) => r.data)
    .map((r) => {
      const p = r.data!;
      return {
        id: p.id,
        slug: p.slug,
        name: p.name,
        brand: p.brand,
        gender: p.gender,
        category_slug: p.category.slug,
        category_name: p.category.name,
        base_price: p.base_price,
        sale_price: p.sale_price,
        effective_price: p.effective_price,
        primary_image: p.variants[0]?.image_url ?? "",
        available_colors: p.available_colors.map((c) => c.hex),
        is_featured: p.is_featured,
        in_stock: p.variants.some((v) => v.inventory_quantity > 0),
      };
    });

  return { items, isLoading: results.some((r) => r.isLoading) };
}

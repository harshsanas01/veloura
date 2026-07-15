import { apiClient } from "@/services/apiClient";
import type { Product, ProductFacets, ProductFilters, ProductListItem, ProductListResponse } from "@/types";

export const productsApi = {
  list: (filters: ProductFilters) =>
    apiClient
      .get<ProductListResponse>("/products", {
        params: filters,
        paramsSerializer: { indexes: null },
      })
      .then((r) => r.data),

  getBySlug: (slug: string) => apiClient.get<Product>(`/products/${slug}`).then((r) => r.data),

  getRelated: (productId: string) =>
    apiClient.get<ProductListItem[]>(`/products/${productId}/related`).then((r) => r.data),

  getFacets: () => apiClient.get<ProductFacets>("/products/facets").then((r) => r.data),
};

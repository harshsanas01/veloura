import { apiClient } from "@/services/apiClient";
import type { Gender, ProductListItem } from "@/types";

export const recommendationsApi = {
  trending: (gender?: Gender, limit = 8) =>
    apiClient
      .get<ProductListItem[]>("/recommendations/trending", { params: { gender, limit } })
      .then((r) => r.data),

  alsoBought: (productId: string, limit = 4) =>
    apiClient
      .get<ProductListItem[]>(`/products/${productId}/also-bought`, { params: { limit } })
      .then((r) => r.data),

  completeTheLook: (productId: string, limit = 4) =>
    apiClient
      .get<ProductListItem[]>(`/products/${productId}/complete-the-look`, { params: { limit } })
      .then((r) => r.data),
};

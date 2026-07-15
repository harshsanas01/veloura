import { apiClient } from "@/services/apiClient";
import type { FitFeedback, Review, ReviewListResponse, ReviewSort } from "@/types";

export const reviewsApi = {
  list: (productId: string, sort: ReviewSort = "newest") =>
    apiClient
      .get<ReviewListResponse>(`/products/${productId}/reviews`, { params: { sort } })
      .then((r) => r.data),

  create: (
    productId: string,
    payload: {
      rating: number;
      title: string;
      body: string;
      fit_feedback?: FitFeedback;
      size_purchased?: string;
    },
  ) => apiClient.post<Review>(`/products/${productId}/reviews`, payload).then((r) => r.data),

  update: (reviewId: string, payload: Partial<{ rating: number; title: string; body: string }>) =>
    apiClient.patch<Review>(`/reviews/${reviewId}`, payload).then((r) => r.data),

  remove: (reviewId: string) => apiClient.delete<void>(`/reviews/${reviewId}`).then((r) => r.data),

  toggleHelpful: (reviewId: string) =>
    apiClient.post<Review>(`/reviews/${reviewId}/helpful`).then((r) => r.data),
};

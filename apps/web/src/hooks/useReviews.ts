import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getApiErrorMessage } from "@/services/apiClient";
import { reviewsApi } from "@/services/reviewsApi";
import { useToastStore } from "@/store/toastStore";
import type { FitFeedback, ReviewSort } from "@/types";

export function useReviews(productId: string | undefined, sort: ReviewSort = "newest") {
  return useQuery({
    queryKey: ["reviews", productId, sort],
    queryFn: () => reviewsApi.list(productId as string, sort),
    enabled: Boolean(productId),
  });
}

export function useCreateReview(productId: string) {
  const queryClient = useQueryClient();
  const push = useToastStore((s) => s.push);
  return useMutation({
    mutationFn: (payload: {
      rating: number;
      title: string;
      body: string;
      fit_feedback?: FitFeedback;
      size_purchased?: string;
    }) => reviewsApi.create(productId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reviews", productId] });
      push("Thanks for your review!", "success");
    },
    onError: (error) => push(getApiErrorMessage(error, "Could not submit your review."), "error"),
  });
}

export function useUpdateReview(productId: string) {
  const queryClient = useQueryClient();
  const push = useToastStore((s) => s.push);
  return useMutation({
    mutationFn: ({ reviewId, payload }: { reviewId: string; payload: Partial<{ rating: number; title: string; body: string }> }) =>
      reviewsApi.update(reviewId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reviews", productId] });
      push("Review updated.", "success");
    },
    onError: (error) => push(getApiErrorMessage(error), "error"),
  });
}

export function useDeleteReview(productId: string) {
  const queryClient = useQueryClient();
  const push = useToastStore((s) => s.push);
  return useMutation({
    mutationFn: (reviewId: string) => reviewsApi.remove(reviewId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reviews", productId] });
      push("Review deleted.", "info");
    },
    onError: (error) => push(getApiErrorMessage(error), "error"),
  });
}

export function useToggleReviewHelpful(productId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (reviewId: string) => reviewsApi.toggleHelpful(reviewId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["reviews", productId] }),
  });
}

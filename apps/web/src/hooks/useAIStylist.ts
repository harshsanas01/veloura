import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { aiStylistApi } from "@/services/aiStylistApi";

export function useStylistRecommend() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ message, sessionId }: { message: string; sessionId?: string }) =>
      aiStylistApi.recommend(message, sessionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ai-sessions"] });
    },
  });
}

export function useStylistSessions() {
  return useQuery({
    queryKey: ["ai-sessions"],
    queryFn: aiStylistApi.listSessions,
  });
}

export function useStylistSession(sessionId: string | undefined) {
  return useQuery({
    queryKey: ["ai-session", sessionId],
    queryFn: () => aiStylistApi.getSession(sessionId as string),
    enabled: Boolean(sessionId),
  });
}

export function useStylistFeedback() {
  return useMutation({
    mutationFn: ({
      outfitId,
      rating,
    }: {
      outfitId: string;
      rating: "like" | "dislike";
    }) => aiStylistApi.feedback(outfitId, rating),
  });
}

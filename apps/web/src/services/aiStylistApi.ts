import { apiClient } from "@/services/apiClient";
import type { ChatSessionDetail, ChatSessionSummary, StylistResponse } from "@/types";

export const aiStylistApi = {
  recommend: (message: string, sessionId?: string) =>
    apiClient
      .post<StylistResponse>("/ai-stylist/recommend", { message, session_id: sessionId })
      .then((r) => r.data),

  listSessions: () =>
    apiClient.get<ChatSessionSummary[]>("/ai-stylist/sessions").then((r) => r.data),

  getSession: (sessionId: string) =>
    apiClient.get<ChatSessionDetail>(`/ai-stylist/sessions/${sessionId}`).then((r) => r.data),

  feedback: (outfit_id: string, rating: "like" | "dislike", comment?: string) =>
    apiClient.post("/ai-stylist/feedback", { outfit_id, rating, comment }),
};

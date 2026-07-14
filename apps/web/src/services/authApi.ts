import { apiClient } from "@/services/apiClient";
import type { TokenResponse, User } from "@/types";

export const authApi = {
  register: (payload: { email: string; password: string; full_name: string }) =>
    apiClient.post<TokenResponse>("/auth/register", payload).then((r) => r.data),

  login: (payload: { email: string; password: string }) =>
    apiClient.post<TokenResponse>("/auth/login", payload).then((r) => r.data),

  me: () => apiClient.get<User>("/auth/me").then((r) => r.data),
};

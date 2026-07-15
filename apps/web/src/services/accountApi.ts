import { apiClient } from "@/services/apiClient";
import type { Address, AddressInput, StyleProfile, User } from "@/types";

export const accountApi = {
  getProfile: () => apiClient.get<User>("/account/profile").then((r) => r.data),

  updateProfile: (payload: Partial<Pick<User, "first_name" | "last_name" | "email">>) =>
    apiClient.patch<User>("/account/profile", payload).then((r) => r.data),

  changePassword: (payload: {
    current_password: string;
    new_password: string;
    confirm_new_password: string;
  }) => apiClient.post<void>("/account/password", payload).then((r) => r.data),

  deleteAccount: (payload: { password: string; confirm: boolean }) =>
    apiClient.post<void>("/account/delete", payload).then((r) => r.data),

  listAddresses: () => apiClient.get<Address[]>("/account/addresses").then((r) => r.data),

  createAddress: (payload: AddressInput) =>
    apiClient.post<Address>("/account/addresses", payload).then((r) => r.data),

  updateAddress: (id: string, payload: Partial<AddressInput>) =>
    apiClient.patch<Address>(`/account/addresses/${id}`, payload).then((r) => r.data),

  deleteAddress: (id: string) =>
    apiClient.delete<void>(`/account/addresses/${id}`).then((r) => r.data),

  getStyleProfile: () => apiClient.get<StyleProfile>("/account/style-profile").then((r) => r.data),

  updateStyleProfile: (payload: Partial<StyleProfile>) =>
    apiClient.put<StyleProfile>("/account/style-profile", payload).then((r) => r.data),
};

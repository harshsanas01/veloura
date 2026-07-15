import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getApiErrorMessage } from "@/services/apiClient";
import { accountApi } from "@/services/accountApi";
import { useAuthStore } from "@/store/authStore";
import { useToastStore } from "@/store/toastStore";
import type { AddressInput, StyleProfile } from "@/types";

export function useUpdateProfile() {
  const push = useToastStore((s) => s.push);
  const updateUser = useAuthStore((s) => s.updateUser);

  return useMutation({
    mutationFn: accountApi.updateProfile,
    onSuccess: (user) => {
      updateUser(user);
      push("Profile updated.", "success");
    },
    onError: (error) => push(getApiErrorMessage(error, "Could not update profile."), "error"),
  });
}

export function useChangePassword() {
  const push = useToastStore((s) => s.push);
  return useMutation({
    mutationFn: accountApi.changePassword,
    onSuccess: () => push("Password updated.", "success"),
    onError: (error) => push(getApiErrorMessage(error, "Could not change password."), "error"),
  });
}

export function useDeleteAccount() {
  const push = useToastStore((s) => s.push);
  const logout = useAuthStore((s) => s.logout);
  return useMutation({
    mutationFn: accountApi.deleteAccount,
    onSuccess: () => {
      logout();
      push("Your account has been deleted.", "info");
    },
    onError: (error) => push(getApiErrorMessage(error, "Could not delete account."), "error"),
  });
}

export function useAddresses() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  return useQuery({
    queryKey: ["addresses"],
    queryFn: accountApi.listAddresses,
    enabled: isAuthenticated,
  });
}

export function useAddressMutations() {
  const queryClient = useQueryClient();
  const push = useToastStore((s) => s.push);
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["addresses"] });

  const create = useMutation({
    mutationFn: (payload: AddressInput) => accountApi.createAddress(payload),
    onSuccess: () => {
      invalidate();
      push("Address added.", "success");
    },
    onError: (error) => push(getApiErrorMessage(error), "error"),
  });

  const update = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<AddressInput> }) =>
      accountApi.updateAddress(id, payload),
    onSuccess: () => {
      invalidate();
      push("Address updated.", "success");
    },
    onError: (error) => push(getApiErrorMessage(error), "error"),
  });

  const remove = useMutation({
    mutationFn: (id: string) => accountApi.deleteAddress(id),
    onSuccess: () => {
      invalidate();
      push("Address removed.", "info");
    },
    onError: (error) => push(getApiErrorMessage(error), "error"),
  });

  return { create, update, remove };
}

export function useStyleProfile() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  return useQuery({
    queryKey: ["style-profile"],
    queryFn: accountApi.getStyleProfile,
    enabled: isAuthenticated,
  });
}

export function useUpdateStyleProfile() {
  const queryClient = useQueryClient();
  const push = useToastStore((s) => s.push);
  return useMutation({
    mutationFn: (payload: Partial<StyleProfile>) => accountApi.updateStyleProfile(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["style-profile"] });
      push("Style profile saved.", "success");
    },
    onError: (error) => push(getApiErrorMessage(error, "Could not save style profile."), "error"),
  });
}

import { useMutation } from "@tanstack/react-query";

import { authApi } from "@/services/authApi";
import { getApiErrorMessage } from "@/services/apiClient";
import { useAuthStore } from "@/store/authStore";
import { useToastStore } from "@/store/toastStore";

export function useLogin() {
  const setSession = useAuthStore((s) => s.setSession);
  const push = useToastStore((s) => s.push);

  return useMutation({
    mutationFn: authApi.login,
    onSuccess: (data) => {
      setSession(data.access_token, data.user);
      push(`Welcome back, ${data.user.full_name.split(" ")[0]}.`, "success");
    },
    onError: (error) => push(getApiErrorMessage(error, "Invalid email or password."), "error"),
  });
}

export function useRegister() {
  const setSession = useAuthStore((s) => s.setSession);
  const push = useToastStore((s) => s.push);

  return useMutation({
    mutationFn: authApi.register,
    onSuccess: (data) => {
      setSession(data.access_token, data.user);
      push(`Welcome to Veloura, ${data.user.full_name.split(" ")[0]}.`, "success");
    },
    onError: (error) => push(getApiErrorMessage(error, "Could not create your account."), "error"),
  });
}

export function useCurrentUser() {
  return useAuthStore((s) => s.user);
}

export function useIsAuthenticated() {
  return useAuthStore((s) => s.isAuthenticated);
}

export function useIsAdmin() {
  return useAuthStore((s) => s.user?.role === "admin");
}

export function useLogout() {
  const logout = useAuthStore((s) => s.logout);
  return logout;
}

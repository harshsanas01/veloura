import { create } from "zustand";

import type { User } from "@/types";

const TOKEN_STORAGE_KEY = "veloura_access_token";
const USER_STORAGE_KEY = "veloura_user";

/**
 * Token persistence is isolated behind this store so the storage mechanism can
 * later move from localStorage to secure HTTP-only cookies without touching
 * every call site that needs the current user or auth status.
 */
interface AuthState {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  setSession: (token: string, user: User) => void;
  updateUser: (user: User) => void;
  logout: () => void;
}

function loadStoredUser(): User | null {
  const raw = localStorage.getItem(USER_STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem(TOKEN_STORAGE_KEY),
  user: loadStoredUser(),
  isAuthenticated: Boolean(localStorage.getItem(TOKEN_STORAGE_KEY)),
  setSession: (token, user) => {
    localStorage.setItem(TOKEN_STORAGE_KEY, token);
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
    set({ token, user, isAuthenticated: true });
  },
  updateUser: (user) => {
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
    set({ user });
  },
  logout: () => {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    localStorage.removeItem(USER_STORAGE_KEY);
    set({ token: null, user: null, isAuthenticated: false });
  },
}));

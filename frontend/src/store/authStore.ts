import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User } from "@/types";
import { authApi } from "@/api/auth";
import { clearAuth } from "@/api/client";

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;

  setTokens: (access: string, refresh: string) => void;
  setUser: (user: User) => void;
  login: (access: string, refresh: string, user: User) => void;
  logout: () => Promise<void>;
  updateUser: (updates: Partial<User>) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,

      setTokens: (access, refresh) => {
        localStorage.setItem("access_token", access);
        localStorage.setItem("refresh_token", refresh);
        set({ accessToken: access, refreshToken: refresh });
      },

      setUser: (user) => set({ user, isAuthenticated: true }),

      login: (access, refresh, user) => {
        localStorage.setItem("access_token", access);
        localStorage.setItem("refresh_token", refresh);
        set({
          accessToken: access,
          refreshToken: refresh,
          user,
          isAuthenticated: true,
        });
      },

      logout: async () => {
        const { refreshToken } = get();
        try {
          if (refreshToken) {
            await authApi.logout(refreshToken);
          }
        } catch {
          // Игнорируем ошибки при logout
        } finally {
          set({ user: null, accessToken: null, refreshToken: null, isAuthenticated: false });
          clearAuth();
        }
      },

      updateUser: (updates) => {
        const { user } = get();
        if (user) set({ user: { ...user, ...updates } });
      },
    }),
    {
      name: "docflow-auth",
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

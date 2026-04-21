import { apiClient } from "./client";
import type { LoginRequest, RegisterRequest, TokenResponse, User } from "@/types";

export const authApi = {
  register: async (data: RegisterRequest): Promise<TokenResponse> => {
    const response = await apiClient.post<TokenResponse>("/auth/register", data);
    return response.data;
  },

  login: async (data: LoginRequest): Promise<TokenResponse> => {
    const response = await apiClient.post<TokenResponse>("/auth/login", data);
    return response.data;
  },

  logout: async (refreshToken: string): Promise<void> => {
    await apiClient.post("/auth/logout", { refresh_token: refreshToken });
  },

  getMe: async (): Promise<User> => {
    const response = await apiClient.get<User>("/auth/me");
    return response.data;
  },

  refresh: async (refreshToken: string): Promise<TokenResponse> => {
    const response = await apiClient.post<TokenResponse>("/auth/refresh", {
      refresh_token: refreshToken,
    });
    return response.data;
  },
};

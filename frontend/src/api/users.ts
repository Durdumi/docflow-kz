import { apiClient } from "./client";
import type { User } from "@/types";

export const usersApi = {
  list: async (): Promise<User[]> => {
    const response = await apiClient.get<User[]>("/users");
    return response.data;
  },

  invite: async (data: {
    email: string;
    first_name: string;
    last_name: string;
    role: string;
  }): Promise<User> => {
    const response = await apiClient.post<User>("/users/invite", data);
    return response.data;
  },

  changeRole: async (userId: string, role: string): Promise<User> => {
    const response = await apiClient.patch<User>(
      `/users/${userId}/role?role=${role}`
    );
    return response.data;
  },

  deactivate: async (userId: string): Promise<void> => {
    await apiClient.patch(`/users/${userId}/deactivate`);
  },

  getProfile: async (): Promise<User> => {
    const response = await apiClient.get<User>("/users/me/profile");
    return response.data;
  },

  updateProfile: async (data: Partial<User>): Promise<User> => {
    const response = await apiClient.patch<User>("/users/me/profile", data);
    return response.data;
  },
};

export const organizationsApi = {
  getMe: async () => {
    const response = await apiClient.get("/organizations/me");
    return response.data;
  },
  updateMe: async (data: Record<string, unknown>) => {
    const response = await apiClient.patch("/organizations/me", data);
    return response.data;
  },
};

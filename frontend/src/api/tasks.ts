import { apiClient } from "./client";

export const tasksApi = {
  list: async (status?: string) => {
    const response = await apiClient.get("/tasks", {
      params: status ? { status_filter: status } : {},
    });
    return response.data;
  },
  create: async (data: any) => {
    const response = await apiClient.post("/tasks", data);
    return response.data;
  },
  update: async (id: string, data: any) => {
    const response = await apiClient.patch(`/tasks/${id}`, data);
    return response.data;
  },
  delete: async (id: string) => {
    await apiClient.delete(`/tasks/${id}`);
  },
};

export const calendarApi = {
  list: async (year?: number, month?: number) => {
    const response = await apiClient.get("/calendar", {
      params: { year, month },
    });
    return response.data;
  },
  create: async (data: any) => {
    const response = await apiClient.post("/calendar", data);
    return response.data;
  },
  update: async (id: string, data: any) => {
    const response = await apiClient.patch(`/calendar/${id}`, data);
    return response.data;
  },
  delete: async (id: string) => {
    await apiClient.delete(`/calendar/${id}`);
  },
};

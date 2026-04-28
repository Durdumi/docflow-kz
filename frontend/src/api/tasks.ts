import { apiClient } from "./client";

export const tasksApi = {
  list: async (status?: string, boardId?: string) => {
    const params: Record<string, string> = {};
    if (status) params.status_filter = status;
    if (boardId) params.board_id = boardId;
    const response = await apiClient.get("/tasks", { params });
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

export const boardApi = {
  getColumns: async () => {
    const response = await apiClient.get("/board/columns");
    return response.data;
  },
  createColumn: async (data: any) => {
    const response = await apiClient.post("/board/columns", data);
    return response.data;
  },
  updateColumn: async (id: string, data: any) => {
    const response = await apiClient.patch(`/board/columns/${id}`, data);
    return response.data;
  },
  deleteColumn: async (id: string) => {
    await apiClient.delete(`/board/columns/${id}`);
  },
  getLabels: async () => {
    const response = await apiClient.get("/board/labels");
    return response.data;
  },
  createLabel: async (data: { color: string; name: string }) => {
    const response = await apiClient.post("/board/labels", data);
    return response.data;
  },
  deleteLabel: async (id: string) => {
    await apiClient.delete(`/board/labels/${id}`);
  },
};

export const activityApi = {
  getTaskActivity: async (taskId: string) => {
    const response = await apiClient.get(`/tasks/${taskId}/activity`);
    return response.data;
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

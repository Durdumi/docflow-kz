import { apiClient } from "./client";
import type { Report, ReportCreate } from "@/types";

export const reportsApi = {
  create: async (data: ReportCreate): Promise<Report> => {
    const response = await apiClient.post<Report>("/reports", data);
    return response.data;
  },

  list: async (page = 1, pageSize = 20): Promise<{ items: Report[]; page: number }> => {
    const response = await apiClient.get("/reports", { params: { page, page_size: pageSize } });
    return response.data;
  },

  getById: async (id: string): Promise<Report> => {
    const response = await apiClient.get<Report>(`/reports/${id}`);
    return response.data;
  },

  download: async (id: string): Promise<Blob> => {
    const response = await apiClient.get(`/reports/${id}/download`, {
      responseType: "blob",
    });
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/reports/${id}`);
  },
};

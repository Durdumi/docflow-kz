import { apiClient } from "./client";

export const importsApi = {
  upload: async (file: File, name: string, category?: string): Promise<any> => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("name", name);
    if (category) formData.append("category", category);
    const response = await apiClient.post("/imports", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return response.data;
  },

  list: async (page = 1, pageSize = 20): Promise<any> => {
    const response = await apiClient.get("/imports", {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },

  getById: async (id: string): Promise<any> => {
    const response = await apiClient.get(`/imports/${id}`);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/imports/${id}`);
  },
};

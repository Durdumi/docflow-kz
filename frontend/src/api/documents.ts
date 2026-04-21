import { apiClient } from "./client";

export const documentsApi = {
  list: async (params?: {
    page?: number;
    page_size?: number;
    status?: string;
    search?: string;
  }) => {
    const response = await apiClient.get("/documents", { params });
    return response.data;
  },

  getById: async (id: string) => {
    const response = await apiClient.get(`/documents/${id}`);
    return response.data;
  },

  create: async (data: {
    title: string;
    template_id?: string | null;
    data?: Record<string, unknown>;
    status?: string;
  }) => {
    const response = await apiClient.post("/documents", data);
    return response.data;
  },

  update: async (
    id: string,
    data: { title?: string; data?: Record<string, unknown> }
  ) => {
    // Backend uses PUT for full document update
    const response = await apiClient.put(`/documents/${id}`, data);
    return response.data;
  },

  delete: async (id: string) => {
    await apiClient.delete(`/documents/${id}`);
  },

  changeStatus: async (id: string, status: string) => {
    const response = await apiClient.patch(`/documents/${id}/status`, { status });
    return response.data;
  },
};

export interface TemplateField {
  id: string;
  name: string;
  label: string;
  type: "text" | "number" | "date" | "select" | "textarea" | "checkbox";
  required: boolean;
  options?: string[];
  default_value?: string;
}

export interface TemplateShort {
  id: string;
  name: string;
  category: string;
  fields: TemplateField[];
}

export const templatesApi = {
  list: async (params?: { page?: number; page_size?: number; search?: string }) => {
    const response = await apiClient.get("/templates", { params });
    return response.data;
  },

  listShort: async (): Promise<TemplateShort[]> => {
    const response = await apiClient.get("/templates/all-short");
    return response.data;
  },

  getById: async (id: string) => {
    const response = await apiClient.get(`/templates/${id}`);
    return response.data;
  },

  create: async (data: {
    name: string;
    description?: string;
    category: string;
    fields: TemplateField[];
  }) => {
    const response = await apiClient.post("/templates", data);
    return response.data;
  },

  update: async (
    id: string,
    data: {
      name?: string;
      description?: string;
      category?: string;
      fields?: TemplateField[];
      is_active?: boolean;
    }
  ) => {
    // Backend uses PUT for template update
    const response = await apiClient.put(`/templates/${id}`, data);
    return response.data;
  },

  delete: async (id: string) => {
    await apiClient.delete(`/templates/${id}`);
  },
};

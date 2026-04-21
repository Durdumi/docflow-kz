import { apiClient } from "./client";
import type {
  Document,
  DocumentTemplate,
  PaginatedResponse,
  TemplateField,
} from "@/types";

// ─── Template Requests ────────────────────────────────────────────────────────
export interface CreateTemplateRequest {
  name: string;
  description?: string;
  category: string;
  fields: TemplateField[];
}

export interface UpdateTemplateRequest {
  name?: string;
  description?: string;
  category?: string;
  fields?: TemplateField[];
  is_active?: boolean;
}

export interface ListTemplatesParams {
  page?: number;
  page_size?: number;
  category?: string;
  search?: string;
  active_only?: boolean;
}

// ─── Document Requests ────────────────────────────────────────────────────────
export interface CreateDocumentRequest {
  title: string;
  template_id?: string;
  data?: Record<string, unknown>;
  status?: string;
}

export interface UpdateDocumentRequest {
  title?: string;
  data?: Record<string, unknown>;
}

export interface ListDocumentsParams {
  page?: number;
  page_size?: number;
  status?: string;
  template_id?: string;
  search?: string;
  my_only?: boolean;
}

// ─── API ─────────────────────────────────────────────────────────────────────
export const templatesApi = {
  list: async (params?: ListTemplatesParams): Promise<PaginatedResponse<DocumentTemplate>> => {
    const res = await apiClient.get<PaginatedResponse<DocumentTemplate>>("/templates", { params });
    return res.data;
  },

  listShort: async (): Promise<DocumentTemplate[]> => {
    const res = await apiClient.get<DocumentTemplate[]>("/templates/all-short");
    return res.data;
  },

  get: async (id: string): Promise<DocumentTemplate> => {
    const res = await apiClient.get<DocumentTemplate>(`/templates/${id}`);
    return res.data;
  },

  create: async (data: CreateTemplateRequest): Promise<DocumentTemplate> => {
    const res = await apiClient.post<DocumentTemplate>("/templates", data);
    return res.data;
  },

  update: async (id: string, data: UpdateTemplateRequest): Promise<DocumentTemplate> => {
    const res = await apiClient.put<DocumentTemplate>(`/templates/${id}`, data);
    return res.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/templates/${id}`);
  },
};

export const documentsApi = {
  list: async (params?: ListDocumentsParams): Promise<PaginatedResponse<Document>> => {
    const res = await apiClient.get<PaginatedResponse<Document>>("/documents", { params });
    return res.data;
  },

  get: async (id: string): Promise<Document> => {
    const res = await apiClient.get<Document>(`/documents/${id}`);
    return res.data;
  },

  create: async (data: CreateDocumentRequest): Promise<Document> => {
    const res = await apiClient.post<Document>("/documents", data);
    return res.data;
  },

  update: async (id: string, data: UpdateDocumentRequest): Promise<Document> => {
    const res = await apiClient.put<Document>(`/documents/${id}`, data);
    return res.data;
  },

  updateStatus: async (id: string, status: string): Promise<Document> => {
    const res = await apiClient.patch<Document>(`/documents/${id}/status`, { status });
    return res.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/documents/${id}`);
  },
};

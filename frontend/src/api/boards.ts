import { apiClient as api } from "./client";

export interface Board {
  id: string;
  name: string;
  description: string | null;
  color: string;
  is_archived: boolean;
  created_at: string;
}

export const boardsApi = {
  list: () => api.get<Board[]>("/boards").then((r) => r.data),
  create: (data: { name: string; description?: string; color?: string }) =>
    api.post<Board>("/boards", data).then((r) => r.data),
  update: (id: string, data: Partial<Board>) =>
    api.patch<Board>(`/boards/${id}`, data).then((r) => r.data),
  remove: (id: string) => api.delete(`/boards/${id}`),
};

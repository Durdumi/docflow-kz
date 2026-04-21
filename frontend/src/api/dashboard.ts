import { apiClient } from "./client";

export interface DashboardStats {
  total_documents: number;
  documents_this_month: number;
  total_reports: number;
  reports_this_month: number;
  pending_reports: number;
  recent_documents: Array<{
    id: string;
    title: string;
    status: string;
    created_at: string;
  }>;
  recent_reports: Array<{
    id: string;
    title: string;
    status: string;
    format: string;
    created_at: string;
  }>;
}

export const dashboardApi = {
  getStats: async (): Promise<DashboardStats> => {
    const [docsRes, reportsRes] = await Promise.all([
      apiClient.get("/documents", { params: { page: 1, page_size: 5 } }),
      apiClient.get("/reports", { params: { page: 1, page_size: 5 } }),
    ]);
    const docs = docsRes.data;
    const reports = reportsRes.data;
    return {
      total_documents: docs.total ?? docs.items?.length ?? 0,
      documents_this_month: docs.items?.length ?? 0,
      total_reports: reports.total ?? reports.items?.length ?? 0,
      reports_this_month: reports.items?.length ?? 0,
      pending_reports:
        reports.items?.filter((r: { status: string }) =>
          ["pending", "generating"].includes(r.status)
        ).length ?? 0,
      recent_documents: docs.items?.slice(0, 5) ?? [],
      recent_reports: reports.items?.slice(0, 5) ?? [],
    };
  },
};

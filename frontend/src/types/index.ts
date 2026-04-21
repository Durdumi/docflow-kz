// ─── Enums ────────────────────────────────────────────────────────────────────
export type UserRole = "super_admin" | "org_admin" | "manager" | "user";
export type OrgPlan = "free" | "starter" | "business" | "enterprise" | "trial";
export type OrgStatus = "active" | "suspended" | "trial";
export type DocumentStatus = "draft" | "active" | "archived" | "deleted";
export type ReportStatus = "pending" | "generating" | "ready" | "failed";

// ─── Auth ─────────────────────────────────────────────────────────────────────
export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  middle_name?: string;
  phone?: string;
  role: UserRole;
  is_active: boolean;
  is_verified: boolean;
  avatar_url?: string;
  organization_id?: string;
  created_at: string;
  last_login_at?: string;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  plan: OrgPlan;
  status: OrgStatus;
  contact_email: string;
  contact_phone?: string;
  country: string;
  city?: string;
  bin_number?: string;
  locale: string;
  timezone: string;
  max_users: number;
  max_documents: number;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

// ─── Auth Requests ────────────────────────────────────────────────────────────
export interface RegisterRequest {
  organization_name: string;
  organization_email: string;
  organization_phone?: string;
  city?: string;
  bin_number?: string;
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  middle_name?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

// ─── Documents ────────────────────────────────────────────────────────────────
export interface DocumentTemplate {
  id: string;
  name: string;
  description?: string;
  category: string;
  fields: TemplateField[];
  created_at: string;
  updated_at: string;
}

export interface TemplateField {
  id: string;
  name: string;
  label: string;
  type: "text" | "number" | "date" | "select" | "textarea" | "checkbox";
  required: boolean;
  options?: string[];
  default_value?: string;
}

export interface Document {
  id: string;
  title: string;
  template_id?: string;
  status: DocumentStatus;
  data: Record<string, unknown>;
  file_url?: string;
  created_by_id: string;
  created_at: string;
  updated_at: string;
}

// ─── Reports ──────────────────────────────────────────────────────────────────
export type ReportFormat = "pdf" | "excel" | "word";

export interface Report {
  id: string;
  title: string;
  type: string;
  format: ReportFormat;
  status: ReportStatus;
  period_from?: string;
  period_to?: string;
  file_url?: string;
  file_size?: number;
  error_message?: string;
  created_by_id: string;
  organization_id?: string;
  created_at: string;
  updated_at?: string;
  completed_at?: string;
}

export interface ReportCreate {
  title: string;
  type: string;
  format?: ReportFormat;
  period_from?: string;
  period_to?: string;
  parameters?: Record<string, unknown>;
}

// ─── API Response Wrappers ────────────────────────────────────────────────────
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface ApiError {
  detail: string;
  status_code?: number;
}

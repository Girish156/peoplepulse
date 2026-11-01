import type {
  AdminJob,
  AuditEvent,
  CheckIn,
  Competency,
  DashboardMetrics,
  DevelopmentPlan,
  Employee,
  Feedback,
  Goal,
  Issue,
  Review,
  ReviewCycle,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("pp_token");
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string> | undefined),
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || body.message || JSON.stringify(body);
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  health: () => request<{ status: string }>("/api/v1/health"),
  login: (email: string, password: string) =>
    request<{
      access_token: string;
      token_type: string;
      role: string;
      name: string;
      email: string;
      employee_id: string | null;
    }>("/api/v1/auth/token", { method: "POST", body: JSON.stringify({ email, password }) }),
  dashboard: () => request<DashboardMetrics>("/api/v1/dashboard"),
  employees: (q?: { skip?: number; limit?: number; search?: string; department?: string }) => {
    const p = new URLSearchParams();
    if (q?.skip != null) p.set("skip", String(q.skip));
    if (q?.limit != null) p.set("limit", String(q.limit));
    if (q?.search) p.set("search", q.search);
    if (q?.department) p.set("department", q.department);
    const qs = p.toString();
    return request<Employee[]>(`/api/v1/employees${qs ? `?${qs}` : ""}`);
  },
  employee: (id: string) => request<Employee>(`/api/v1/employees/${encodeURIComponent(id)}`),
  goals: (q?: { skip?: number; limit?: number; employee_id?: string; cycle_id?: string; status_filter?: string }) => {
    const p = new URLSearchParams();
    Object.entries(q || {}).forEach(([k, v]) => {
      if (v != null && v !== "") p.set(k, String(v));
    });
    const qs = p.toString();
    return request<Goal[]>(`/api/v1/goals${qs ? `?${qs}` : ""}`);
  },
  goal: (id: string) => request<Goal>(`/api/v1/goals/${encodeURIComponent(id)}`),
  createGoal: (payload: Record<string, unknown>) =>
    request<Goal>("/api/v1/goals", { method: "POST", body: JSON.stringify(payload) }),
  updateGoal: (id: string, payload: Record<string, unknown>) =>
    request<Goal>(`/api/v1/goals/${encodeURIComponent(id)}`, { method: "PATCH", body: JSON.stringify(payload) }),
  createCheckIn: (goalId: string, payload: Record<string, unknown>) =>
    request<CheckIn>(`/api/v1/goals/${encodeURIComponent(goalId)}/check-ins`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  checkIns: (q?: { skip?: number; limit?: number; employee_id?: string; goal_id?: string }) => {
    const p = new URLSearchParams();
    Object.entries(q || {}).forEach(([k, v]) => {
      if (v != null && v !== "") p.set(k, String(v));
    });
    const qs = p.toString();
    return request<CheckIn[]>(`/api/v1/check-ins${qs ? `?${qs}` : ""}`);
  },
  competencies: () => request<Competency[]>("/api/v1/competencies"),
  feedback: (q?: { skip?: number; limit?: number; subject_id?: string; author_id?: string; feedback_type?: string }) => {
    const p = new URLSearchParams();
    Object.entries(q || {}).forEach(([k, v]) => {
      if (v != null && v !== "") p.set(k, String(v));
    });
    const qs = p.toString();
    return request<Feedback[]>(`/api/v1/feedback${qs ? `?${qs}` : ""}`);
  },
  createFeedback: (payload: Record<string, unknown>) =>
    request<Feedback>("/api/v1/feedback", { method: "POST", body: JSON.stringify(payload) }),
  reviewCycles: () => request<ReviewCycle[]>("/api/v1/review-cycles"),
  createCycle: (payload: Record<string, unknown>) =>
    request<ReviewCycle>("/api/v1/review-cycles", { method: "POST", body: JSON.stringify(payload) }),
  transitionCycle: (id: string, payload: Record<string, unknown>) =>
    request<ReviewCycle>(`/api/v1/review-cycles/${encodeURIComponent(id)}/transition`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  reviews: (q?: { skip?: number; limit?: number; employee_id?: string; cycle_id?: string }) => {
    const p = new URLSearchParams();
    Object.entries(q || {}).forEach(([k, v]) => {
      if (v != null && v !== "") p.set(k, String(v));
    });
    const qs = p.toString();
    return request<Review[]>(`/api/v1/reviews${qs ? `?${qs}` : ""}`);
  },
  review: (id: string) => request<Review>(`/api/v1/reviews/${encodeURIComponent(id)}`),
  createReview: (payload: Record<string, unknown>) =>
    request<Review>("/api/v1/reviews", { method: "POST", body: JSON.stringify(payload) }),
  submitReview: (id: string, payload: Record<string, unknown>) =>
    request<Review>(`/api/v1/reviews/${encodeURIComponent(id)}/submit`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  plans: (q?: { skip?: number; limit?: number; employee_id?: string }) => {
    const p = new URLSearchParams();
    Object.entries(q || {}).forEach(([k, v]) => {
      if (v != null && v !== "") p.set(k, String(v));
    });
    const qs = p.toString();
    return request<DevelopmentPlan[]>(`/api/v1/development-plans${qs ? `?${qs}` : ""}`);
  },
  createPlan: (payload: Record<string, unknown>) =>
    request<DevelopmentPlan>("/api/v1/development-plans", { method: "POST", body: JSON.stringify(payload) }),
  approvePlan: (id: string) =>
    request<DevelopmentPlan>(`/api/v1/development-plans/${encodeURIComponent(id)}/approve`, { method: "POST" }),
  issues: (q?: { skip?: number; limit?: number; issue_type?: string; severity?: string; resolution_status?: string }) => {
    const p = new URLSearchParams();
    Object.entries(q || {}).forEach(([k, v]) => {
      if (v != null && v !== "") p.set(k, String(v));
    });
    const qs = p.toString();
    return request<Issue[]>(`/api/v1/issues${qs ? `?${qs}` : ""}`);
  },
  issue: (id: string) => request<Issue>(`/api/v1/issues/${encodeURIComponent(id)}`),
  resolveIssue: (id: string, payload: Record<string, unknown>) =>
    request<Issue>(`/api/v1/issues/${encodeURIComponent(id)}/resolve`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  audit: (q?: { skip?: number; limit?: number; entity_type?: string; action?: string }) => {
    const p = new URLSearchParams();
    Object.entries(q || {}).forEach(([k, v]) => {
      if (v != null && v !== "") p.set(k, String(v));
    });
    const qs = p.toString();
    return request<AuditEvent[]>(`/api/v1/audit${qs ? `?${qs}` : ""}`);
  },
  auditForEntity: (entityType: string, entityId: string) =>
    request<AuditEvent[]>(`/api/v1/audit/${encodeURIComponent(entityType)}/${encodeURIComponent(entityId)}`),
  validationReport: () => request<Record<string, unknown>>("/api/v1/admin/validation-report"),
  generateData: (mode: string, seed: number) =>
    request<AdminJob>("/api/v1/admin/generate-data", {
      method: "POST",
      body: JSON.stringify({ mode, seed }),
    }),
  job: (id: string) => request<AdminJob>(`/api/v1/admin/jobs/${encodeURIComponent(id)}`),
};

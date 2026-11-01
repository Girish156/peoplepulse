export type Role = "admin" | "hr_partner" | "manager" | "employee" | "peer_reviewer" | "it_operations";

export interface AuthUser {
  access_token: string;
  token_type: string;
  role: Role;
  name: string;
  email: string;
  employee_id: string | null;
}

export interface Employee {
  id: string;
  employee_id: string;
  name: string;
  email: string;
  department: string;
  job_title: string;
  employment_status: string;
  manager_id: string | null;
  manager_name: string | null;
  manager_employee_id: string | null;
  hire_date: string | null;
  termination_date: string | null;
  created_at: string;
  updated_at: string;
}

export interface KeyResult {
  id: string;
  key_result_id: string;
  goal_id: string;
  title: string;
  metric_type: string;
  unit: string | null;
  baseline: number;
  target: number;
  actual: number | null;
  weight: number;
  allowed_progress_scale: number;
  progress_percentage: number | null;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface Goal {
  id: string;
  goal_id: string;
  employee_id: string;
  cycle_id: string;
  employee_name: string | null;
  employee_business_id: string | null;
  cycle_business_id: string | null;
  title: string;
  description: string | null;
  status: string;
  weight: number;
  start_date: string | null;
  due_date: string | null;
  version: number;
  rationale: string | null;
  key_results: KeyResult[];
  progress_percentage: number;
  created_at: string;
  updated_at: string;
}

export interface Evidence {
  id: string;
  evidence_id: string;
  title: string;
  description: string | null;
  url: string | null;
  evidence_type: string;
  created_at: string;
}

export interface CheckIn {
  id: string;
  check_in_id: string;
  employee_id: string;
  goal_id: string;
  cycle_id: string;
  employee_name: string | null;
  employee_business_id: string | null;
  goal_title: string | null;
  check_in_date: string;
  notes: string | null;
  progress_snapshot: Record<string, number> | null;
  status: string;
  evidence: Evidence[];
  created_at: string;
}

export interface Competency {
  id: string;
  competency_id: string;
  name: string;
  description: string;
  rating_scale: number;
  is_active: boolean;
}

export interface Feedback {
  id: string;
  feedback_id: string;
  subject_employee_id: string;
  author_employee_id: string;
  subject_name: string | null;
  author_name: string | null;
  feedback_type: string;
  competency_name: string | null;
  rating: number | null;
  comments: string;
  status: string;
  submitted_at: string;
  created_at: string;
  updated_at: string;
}

export interface ReviewCycle {
  id: string;
  cycle_id: string;
  name: string;
  start_date: string;
  end_date: string;
  status: string;
  version: number;
  closed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReviewParticipant {
  id: string;
  participant_employee_id: string;
  participant_name: string | null;
  role: string;
  is_required: boolean;
  completed_at: string | null;
}

export interface Review {
  id: string;
  review_id: string;
  employee_id: string;
  cycle_id: string;
  reviewer_id: string;
  employee_name: string | null;
  reviewer_name: string | null;
  cycle_name: string | null;
  status: string;
  goal_score: number | null;
  feedback_score: number | null;
  overall_score: number | null;
  summary: string | null;
  submitted_at: string | null;
  version: number;
  participants: ReviewParticipant[];
  created_at: string;
  updated_at: string;
}

export interface DevelopmentPlanAction {
  id: string;
  title: string;
  description: string | null;
  due_date: string | null;
  status: string;
  completed_at: string | null;
}

export interface DevelopmentPlan {
  id: string;
  plan_id: string;
  employee_id: string;
  employee_name: string | null;
  review_id: string | null;
  objectives: string;
  status: string;
  approver_id: string | null;
  approver_name: string | null;
  approved_at: string | null;
  completion_date: string | null;
  actions: DevelopmentPlanAction[];
  version: number;
  created_at: string;
  updated_at: string;
}

export interface Issue {
  id: string;
  issue_id: string;
  issue_type: string;
  entity_type: string;
  entity_id: string;
  severity: string;
  rule_id: string;
  explanation: string;
  expected_value: string | null;
  actual_value: string | null;
  detected_at: string;
  resolution_status: string;
  resolved_at: string | null;
  resolved_by: string | null;
  evidence_refs: unknown[] | null;
  created_at: string;
  updated_at: string;
}

export interface AuditEvent {
  id: string;
  event_id: string;
  actor_employee_id: string | null;
  actor_role: string | null;
  action: string;
  entity_type: string;
  entity_id: string;
  before_state: Record<string, unknown> | null;
  after_state: Record<string, unknown> | null;
  reason: string | null;
  correlation_id: string | null;
  created_at: string;
}

export interface DashboardMetrics {
  total_employees: number;
  active_goals: number;
  avg_goal_progress: number;
  check_in_completion_rate: number;
  total_check_ins: number;
  total_reviews: number;
  completed_reviews: number;
  review_completion_rate: number;
  outstanding_feedback: number;
  unresolved_issues: number;
  issue_severities: Record<string, number>;
  department_breakdown: { department: string; count: number }[];
  recent_audit_events: {
    event_id: string;
    action: string;
    entity_type: string;
    entity_id: string;
    actor_role: string | null;
    reason: string | null;
    created_at: string | null;
  }[];
}

export interface AdminJob {
  job_id: string;
  mode?: string;
  seed?: number;
  status: string;
  output?: string | null;
  error?: string | null;
}

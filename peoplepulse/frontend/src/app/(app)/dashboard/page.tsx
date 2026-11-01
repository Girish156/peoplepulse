"use client";

import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api, ApiError } from "@/lib/api";
import { formatDateTime, formatPercent } from "@/lib/formatters";
import { Skeleton } from "@/components/ui/EmptyState";
import type { DashboardMetrics } from "@/types";

const KPI_HELP = {
  employees: "Count of employees with employment_status = active.",
  goals: "Count of goals with status = active.",
  progress: "Mean weighted goal progress for active goals that have key results. Formula: Σ(capped KR progress × KR weight) / Σ(valid KR weights).",
  checkins: "min(total check-ins / active employees, 1) × 100. Denominator is active employees.",
  reviews: "completed reviews (submitted/approved/completed/calibrated) / total reviews.",
  feedback: "Feedback records still in submitted status (not yet acknowledged).",
  issues: "Issues whose resolution_status is open or investigating.",
};

export default function DashboardPage() {
  const [data, setData] = useState<DashboardMetrics | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .dashboard()
      .then(setData)
      .catch((e) => setError(e instanceof ApiError ? e.detail : "Failed to load dashboard"));
  }, []);

  if (error) return <p className="text-rose-600">{error}</p>;
  if (!data) {
    return (
      <div className="grid gap-4 md:grid-cols-3">
        <Skeleton />
        <Skeleton />
        <Skeleton />
      </div>
    );
  }

  const kpis = [
    { label: "Active employees", value: data.total_employees, help: KPI_HELP.employees },
    { label: "Active goals", value: data.active_goals, help: KPI_HELP.goals },
    { label: "Avg weighted progress", value: formatPercent(data.avg_goal_progress), help: KPI_HELP.progress },
    { label: "Check-in activity", value: formatPercent(data.check_in_completion_rate), help: KPI_HELP.checkins },
    { label: "Review completion", value: formatPercent(data.review_completion_rate), help: KPI_HELP.reviews },
    { label: "Outstanding feedback", value: data.outstanding_feedback, help: KPI_HELP.feedback },
    { label: "Unresolved exceptions", value: data.unresolved_issues, help: KPI_HELP.issues },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <p className="text-sm text-slate-500">All KPIs are computed from the live database. Hover a card for the denominator.</p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {kpis.map((k) => (
          <div key={k.label} className="card p-4" title={k.help}>
            <p className="text-xs uppercase tracking-wide text-slate-500">{k.label}</p>
            <p className="mt-2 text-2xl font-semibold">{k.value}</p>
            <p className="mt-2 text-xs text-slate-400">{k.help}</p>
          </div>
        ))}
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card p-4">
          <h2 className="mb-4 text-sm font-semibold">Headcount by department</h2>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.department_breakdown}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="department" hide />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#4f46e5" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="card p-4">
          <h2 className="mb-4 text-sm font-semibold">Recent audit events</h2>
          <div className="space-y-3">
            {data.recent_audit_events.map((e) => (
              <div key={e.event_id} className="border-b border-slate-100 pb-2 text-sm last:border-0">
                <p className="font-medium">{e.action}</p>
                <p className="text-xs text-slate-500">
                  {e.entity_type} {e.entity_id} · {formatDateTime(e.created_at)}
                </p>
              </div>
            ))}
            {data.recent_audit_events.length === 0 ? <p className="text-sm text-slate-500">No audit events yet.</p> : null}
          </div>
        </div>
      </div>
    </div>
  );
}

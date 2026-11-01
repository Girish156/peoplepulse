"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { Badge, statusTone } from "@/components/ui/Badge";
import { ProgressBar } from "@/components/ui/ProgressBar";
import type { DevelopmentPlan, Employee, Goal, Review } from "@/types";

export default function EmployeeDetailPage() {
  const params = useParams<{ id: string }>();
  const [emp, setEmp] = useState<Employee | null>(null);
  const [goals, setGoals] = useState<Goal[]>([]);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [plans, setPlans] = useState<DevelopmentPlan[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    const id = params.id;
    api
      .employee(id)
      .then(async (employee) => {
        setEmp(employee);
        const [g, r, p] = await Promise.all([
          api.goals({ employee_id: employee.employee_id, limit: 50 }),
          api.reviews({ employee_id: employee.employee_id, limit: 50 }),
          api.plans({ employee_id: employee.employee_id, limit: 50 }),
        ]);
        setGoals(g);
        setReviews(r);
        setPlans(p);
      })
      .catch((e) => setError(e instanceof ApiError ? e.detail : "Not found"));
  }, [params.id]);

  if (error) return <p className="text-rose-600">{error}</p>;
  if (!emp) return <p className="text-sm text-slate-500">Loading…</p>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">{emp.name}</h1>
        <p className="text-sm text-slate-500">
          {emp.employee_id} · {emp.job_title} · {emp.department}
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        <div className="card p-4 text-sm">
          <p>Email: {emp.email}</p>
          <p>Status: <Badge tone={statusTone(emp.employment_status)}>{emp.employment_status}</Badge></p>
          <p>Manager: {emp.manager_name || "—"} ({emp.manager_employee_id || "none"})</p>
          <p>Hire date: {emp.hire_date || "—"}</p>
        </div>
      </div>
      <section className="card p-4">
        <h2 className="mb-3 font-semibold">Goals</h2>
        {goals.map((g) => (
          <Link key={g.id} href={`/goals/${g.goal_id}`} className="mb-3 block rounded-lg border border-slate-100 p-3">
            <div className="flex justify-between text-sm">
              <span>{g.title}</span>
              <span>{g.progress_percentage.toFixed(1)}%</span>
            </div>
            <ProgressBar value={g.progress_percentage} />
          </Link>
        ))}
        {goals.length === 0 ? <p className="text-sm text-slate-500">No goals.</p> : null}
      </section>
      <section className="card p-4">
        <h2 className="mb-3 font-semibold">Reviews</h2>
        {reviews.map((r) => (
          <Link key={r.id} href={`/reviews/${r.review_id}`} className="mb-2 block text-sm text-indigo-700">
            {r.review_id} · {r.cycle_name} · {r.status}
          </Link>
        ))}
        {reviews.length === 0 ? <p className="text-sm text-slate-500">No reviews.</p> : null}
      </section>
      <section className="card p-4">
        <h2 className="mb-3 font-semibold">Development plans</h2>
        {plans.map((p) => (
          <p key={p.id} className="text-sm">
            {p.plan_id} · {p.status}
          </p>
        ))}
        {plans.length === 0 ? <p className="text-sm text-slate-500">No plans.</p> : null}
      </section>
    </div>
  );
}

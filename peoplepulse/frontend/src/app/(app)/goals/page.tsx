"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { useToast } from "@/components/ui/Toast";
import { Badge, statusTone } from "@/components/ui/Badge";
import { EmptyState, Skeleton } from "@/components/ui/EmptyState";
import { ProgressBar } from "@/components/ui/ProgressBar";
import type { Employee, Goal, ReviewCycle } from "@/types";

export default function GoalsPage() {
  const { push } = useToast();
  const [goals, setGoals] = useState<Goal[] | null>(null);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [cycles, setCycles] = useState<ReviewCycle[]>([]);
  const [status, setStatus] = useState("");
  const [form, setForm] = useState({
    employee_employee_id: "",
    cycle_cycle_id: "",
    title: "",
    description: "",
    kr1_title: "KR 1",
    kr1_target: "10",
    kr1_actual: "8",
    kr1_weight: "0.6",
    kr2_title: "KR 2",
    kr2_target: "20",
    kr2_actual: "15",
    kr2_weight: "0.4",
  });
  const [saving, setSaving] = useState(false);

  function load() {
    api.goals({ limit: 50, status_filter: status || undefined }).then(setGoals);
  }

  useEffect(() => {
    load();
    api.employees({ limit: 100 }).then(setEmployees);
    api.reviewCycles().then(setCycles);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function createGoal(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const created = await api.createGoal({
        employee_employee_id: form.employee_employee_id,
        cycle_cycle_id: form.cycle_cycle_id,
        title: form.title,
        description: form.description,
        status: "active",
        key_results: [
          {
            title: form.kr1_title,
            metric_type: "count",
            unit: "items",
            baseline: 0,
            target: Number(form.kr1_target),
            actual: Number(form.kr1_actual),
            weight: Number(form.kr1_weight),
          },
          {
            title: form.kr2_title,
            metric_type: "count",
            unit: "items",
            baseline: 0,
            target: Number(form.kr2_target),
            actual: Number(form.kr2_actual),
            weight: Number(form.kr2_weight),
          },
        ],
      });
      push(`Goal ${created.goal_id} created with ${created.progress_percentage.toFixed(1)}% progress`, "success");
      load();
    } catch (err) {
      push(err instanceof ApiError ? err.detail : "Create failed", "error");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Goals</h1>
        <select
          className="input max-w-40"
          value={status}
          onChange={(e) => {
            setStatus(e.target.value);
            api.goals({ limit: 50, status_filter: e.target.value || undefined }).then(setGoals);
          }}
        >
          <option value="">All statuses</option>
          <option value="draft">draft</option>
          <option value="active">active</option>
          <option value="completed">completed</option>
        </select>
      </div>

      <form onSubmit={createGoal} className="card grid gap-3 p-4 md:grid-cols-2">
        <h2 className="md:col-span-2 font-semibold">Create goal with measurable key results</h2>
        <select className="input" required value={form.employee_employee_id} onChange={(e) => setForm({ ...form, employee_employee_id: e.target.value })}>
          <option value="">Employee</option>
          {employees.map((e) => (
            <option key={e.id} value={e.employee_id}>
              {e.employee_id} — {e.name}
            </option>
          ))}
        </select>
        <select className="input" required value={form.cycle_cycle_id} onChange={(e) => setForm({ ...form, cycle_cycle_id: e.target.value })}>
          <option value="">Review cycle</option>
          {cycles.map((c) => (
            <option key={c.id} value={c.cycle_id}>
              {c.cycle_id} — {c.name} ({c.status})
            </option>
          ))}
        </select>
        <input className="input md:col-span-2" required placeholder="Goal title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
        <textarea className="input md:col-span-2" placeholder="Description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
        <div className="grid grid-cols-4 gap-2 md:col-span-2">
          <input className="input col-span-2" value={form.kr1_title} onChange={(e) => setForm({ ...form, kr1_title: e.target.value })} />
          <input className="input" value={form.kr1_target} onChange={(e) => setForm({ ...form, kr1_target: e.target.value })} placeholder="target" />
          <input className="input" value={form.kr1_actual} onChange={(e) => setForm({ ...form, kr1_actual: e.target.value })} placeholder="actual" />
        </div>
        <div className="grid grid-cols-4 gap-2 md:col-span-2">
          <input className="input col-span-2" value={form.kr2_title} onChange={(e) => setForm({ ...form, kr2_title: e.target.value })} />
          <input className="input" value={form.kr2_target} onChange={(e) => setForm({ ...form, kr2_target: e.target.value })} placeholder="target" />
          <input className="input" value={form.kr2_actual} onChange={(e) => setForm({ ...form, kr2_actual: e.target.value })} placeholder="actual" />
        </div>
        <button className="btn btn-primary w-fit" disabled={saving}>
          {saving ? "Saving…" : "Create goal"}
        </button>
      </form>

      {!goals ? (
        <Skeleton className="h-48" />
      ) : goals.length === 0 ? (
        <EmptyState title="No goals yet" hint="Create a goal above. Progress is calculated from key-result actual/target and weights." />
      ) : (
        <div className="space-y-3">
          {goals.map((g) => (
            <Link key={g.id} href={`/goals/${g.goal_id}`} className="card block p-4 hover:border-indigo-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">{g.title}</p>
                  <p className="text-xs text-slate-500">
                    {g.goal_id} · {g.employee_name} · {g.cycle_business_id}
                  </p>
                </div>
                <Badge tone={statusTone(g.status)}>{g.status}</Badge>
              </div>
              <div className="mt-3">
                <ProgressBar value={g.progress_percentage} />
                <p className="mt-1 text-xs text-slate-500">{g.progress_percentage.toFixed(1)}% weighted progress</p>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

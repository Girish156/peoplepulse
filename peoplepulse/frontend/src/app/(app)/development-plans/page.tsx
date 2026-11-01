"use client";

import { FormEvent, useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { useToast } from "@/components/ui/Toast";
import { Badge, statusTone } from "@/components/ui/Badge";
import { EmptyState, Skeleton } from "@/components/ui/EmptyState";
import type { DevelopmentPlan, Employee } from "@/types";

export default function PlansPage() {
  const { push } = useToast();
  const [rows, setRows] = useState<DevelopmentPlan[] | null>(null);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [form, setForm] = useState({ employee_id: "", objectives: "", action_title: "", due_date: "" });

  function load() {
    api.plans({ limit: 50 }).then(setRows);
  }

  useEffect(() => {
    load();
    api.employees({ limit: 100 }).then(setEmployees);
  }, []);

  async function create(e: FormEvent) {
    e.preventDefault();
    try {
      await api.createPlan({
        employee_id: form.employee_id,
        objectives: form.objectives,
        actions: form.action_title ? [{ title: form.action_title, due_date: form.due_date || null }] : [],
      });
      push("Development plan created", "success");
      load();
    } catch (err) {
      push(err instanceof ApiError ? err.detail : "Create failed", "error");
    }
  }

  async function approve(id: string) {
    if (!confirm("Approve this development plan? This records an audit event.")) return;
    try {
      await api.approvePlan(id);
      push("Plan approved", "success");
      load();
    } catch (err) {
      push(err instanceof ApiError ? err.detail : "Approve failed", "error");
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Development plans</h1>
      <form onSubmit={create} className="card grid gap-3 p-4 md:grid-cols-2">
        <select className="input" required value={form.employee_id} onChange={(e) => setForm({ ...form, employee_id: e.target.value })}>
          <option value="">Employee</option>
          {employees.map((e) => <option key={e.id} value={e.employee_id}>{e.name}</option>)}
        </select>
        <input className="input" placeholder="Action title" value={form.action_title} onChange={(e) => setForm({ ...form, action_title: e.target.value })} />
        <input className="input" type="date" value={form.due_date} onChange={(e) => setForm({ ...form, due_date: e.target.value })} />
        <textarea className="input md:col-span-2" required placeholder="Objectives" value={form.objectives} onChange={(e) => setForm({ ...form, objectives: e.target.value })} />
        <button className="btn btn-primary w-fit">Create plan</button>
      </form>
      {!rows ? (
        <Skeleton className="h-48" />
      ) : rows.length === 0 ? (
        <EmptyState title="No development plans" />
      ) : (
        <div className="space-y-3">
          {rows.map((p) => (
            <div key={p.id} className="card p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-medium">{p.plan_id} · {p.employee_name}</p>
                  <p className="text-sm text-slate-600">{p.objectives}</p>
                  <ul className="mt-2 list-disc pl-5 text-sm text-slate-600">
                    {p.actions.map((a) => (
                      <li key={a.id}>{a.title} · {a.status} · due {a.due_date || "n/a"}</li>
                    ))}
                  </ul>
                </div>
                <div className="space-y-2 text-right">
                  <Badge tone={statusTone(p.status)}>{p.status}</Badge>
                  {p.status !== "completed" ? (
                    <button className="btn btn-secondary" onClick={() => approve(p.plan_id)}>Approve</button>
                  ) : (
                    <p className="text-xs text-slate-500">Approved {p.approved_at}</p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

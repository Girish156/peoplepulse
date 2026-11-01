"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { useToast } from "@/components/ui/Toast";
import { Badge, statusTone } from "@/components/ui/Badge";
import { EmptyState, Skeleton } from "@/components/ui/EmptyState";
import type { Employee, Review, ReviewCycle } from "@/types";

export default function ReviewsPage() {
  const { push } = useToast();
  const [rows, setRows] = useState<Review[] | null>(null);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [cycles, setCycles] = useState<ReviewCycle[]>([]);
  const [form, setForm] = useState({ employee_id: "", reviewer_id: "", cycle_id: "", summary: "" });

  function load() {
    api.reviews({ limit: 50 }).then(setRows);
  }

  useEffect(() => {
    load();
    api.employees({ limit: 100 }).then(setEmployees);
    api.reviewCycles().then(setCycles);
  }, []);

  async function create(e: FormEvent) {
    e.preventDefault();
    try {
      const created = await api.createReview(form);
      push(`Review ${created.review_id} created`, "success");
      load();
    } catch (err) {
      push(err instanceof ApiError ? err.detail : "Create failed", "error");
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Reviews</h1>
      <form onSubmit={create} className="card grid gap-3 p-4 md:grid-cols-2">
        <select className="input" required value={form.employee_id} onChange={(e) => setForm({ ...form, employee_id: e.target.value })}>
          <option value="">Subject employee</option>
          {employees.map((e) => <option key={e.id} value={e.employee_id}>{e.name}</option>)}
        </select>
        <select className="input" required value={form.reviewer_id} onChange={(e) => setForm({ ...form, reviewer_id: e.target.value })}>
          <option value="">Reviewer</option>
          {employees.map((e) => <option key={e.id} value={e.employee_id}>{e.name}</option>)}
        </select>
        <select className="input" required value={form.cycle_id} onChange={(e) => setForm({ ...form, cycle_id: e.target.value })}>
          <option value="">Cycle</option>
          {cycles.map((c) => <option key={c.id} value={c.cycle_id}>{c.name} ({c.status})</option>)}
        </select>
        <input className="input" placeholder="Summary" value={form.summary} onChange={(e) => setForm({ ...form, summary: e.target.value })} />
        <button className="btn btn-primary w-fit">Start review</button>
      </form>
      {!rows ? (
        <Skeleton className="h-48" />
      ) : rows.length === 0 ? (
        <EmptyState title="No reviews" />
      ) : (
        <div className="card overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">Review</th>
                <th className="px-4 py-3">Employee</th>
                <th className="px-4 py-3">Reviewer</th>
                <th className="px-4 py-3">Cycle</th>
                <th className="px-4 py-3">Score</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id} className="border-t border-slate-100">
                  <td className="px-4 py-3">
                    <Link className="text-indigo-700" href={`/reviews/${r.review_id}`}>{r.review_id}</Link>
                  </td>
                  <td className="px-4 py-3">{r.employee_name}</td>
                  <td className="px-4 py-3">{r.reviewer_name}</td>
                  <td className="px-4 py-3">{r.cycle_name}</td>
                  <td className="px-4 py-3">{r.overall_score ?? "—"}</td>
                  <td className="px-4 py-3"><Badge tone={statusTone(r.status)}>{r.status}</Badge></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

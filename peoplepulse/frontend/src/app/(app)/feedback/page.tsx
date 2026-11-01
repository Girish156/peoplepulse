"use client";

import { FormEvent, useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { useToast } from "@/components/ui/Toast";
import { Badge, statusTone } from "@/components/ui/Badge";
import { EmptyState, Skeleton } from "@/components/ui/EmptyState";
import type { Competency, Employee, Feedback } from "@/types";

export default function FeedbackPage() {
  const { push } = useToast();
  const [rows, setRows] = useState<Feedback[] | null>(null);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [comps, setComps] = useState<Competency[]>([]);
  const [typeFilter, setTypeFilter] = useState("");
  const [form, setForm] = useState({
    subject_employee_id: "",
    author_employee_id: "",
    feedback_type: "peer",
    competency_id: "",
    rating: "4",
    comments: "",
  });

  function load() {
    api.feedback({ limit: 50, feedback_type: typeFilter || undefined }).then(setRows);
  }

  useEffect(() => {
    load();
    api.employees({ limit: 100 }).then(setEmployees);
    api.competencies().then(setComps);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function submit(e: FormEvent) {
    e.preventDefault();
    try {
      await api.createFeedback({
        ...form,
        rating: Number(form.rating),
        competency_id: form.competency_id || null,
      });
      push("Feedback submitted", "success");
      load();
    } catch (err) {
      push(err instanceof ApiError ? err.detail : "Submit failed", "error");
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Feedback</h1>
      <p className="text-sm text-slate-500">
        Self feedback requires matching author and subject. Manager feedback must be submitted by the subject&apos;s
        current manager. Peer feedback is recorded with author, subject, timestamp, and competency.
      </p>
      <form onSubmit={submit} className="card grid gap-3 p-4 md:grid-cols-2">
        <select className="input" required value={form.subject_employee_id} onChange={(e) => setForm({ ...form, subject_employee_id: e.target.value })}>
          <option value="">Subject</option>
          {employees.map((e) => (
            <option key={e.id} value={e.employee_id}>{e.name}</option>
          ))}
        </select>
        <select className="input" required value={form.author_employee_id} onChange={(e) => setForm({ ...form, author_employee_id: e.target.value })}>
          <option value="">Author</option>
          {employees.map((e) => (
            <option key={e.id} value={e.employee_id}>{e.name}</option>
          ))}
        </select>
        <select className="input" value={form.feedback_type} onChange={(e) => setForm({ ...form, feedback_type: e.target.value })}>
          <option value="self">self</option>
          <option value="manager">manager</option>
          <option value="peer">peer</option>
        </select>
        <select className="input" value={form.competency_id} onChange={(e) => setForm({ ...form, competency_id: e.target.value })}>
          <option value="">Competency (optional)</option>
          {comps.map((c) => (
            <option key={c.id} value={c.competency_id}>{c.name}</option>
          ))}
        </select>
        <input className="input" type="number" min={1} max={5} value={form.rating} onChange={(e) => setForm({ ...form, rating: e.target.value })} />
        <textarea className="input md:col-span-2" required placeholder="Comments" value={form.comments} onChange={(e) => setForm({ ...form, comments: e.target.value })} />
        <button className="btn btn-primary w-fit">Submit feedback</button>
      </form>
      <select
        className="input max-w-xs"
        value={typeFilter}
        onChange={(e) => {
          setTypeFilter(e.target.value);
          api.feedback({ limit: 50, feedback_type: e.target.value || undefined }).then(setRows);
        }}
      >
        <option value="">All types</option>
        <option value="self">self</option>
        <option value="manager">manager</option>
        <option value="peer">peer</option>
      </select>
      {!rows ? (
        <Skeleton className="h-48" />
      ) : rows.length === 0 ? (
        <EmptyState title="No feedback yet" />
      ) : (
        <div className="space-y-3">
          {rows.map((f) => (
            <div key={f.id} className="card p-4 text-sm">
              <div className="flex justify-between">
                <p className="font-medium">
                  {f.author_name} → {f.subject_name}
                </p>
                <Badge tone={statusTone(f.feedback_type)}>{f.feedback_type}</Badge>
              </div>
              <p className="mt-1 text-slate-600">{f.comments}</p>
              <p className="mt-1 text-xs text-slate-500">
                {f.competency_name || "No competency"} · rating {f.rating ?? "—"} · {f.submitted_at}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

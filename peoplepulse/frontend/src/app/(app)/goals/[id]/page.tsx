"use client";

import { FormEvent, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { useToast } from "@/components/ui/Toast";
import { Badge, statusTone } from "@/components/ui/Badge";
import { ProgressBar } from "@/components/ui/ProgressBar";
import type { AuditEvent, CheckIn, Goal } from "@/types";

export default function GoalDetailPage() {
  const params = useParams<{ id: string }>();
  const { push } = useToast();
  const [goal, setGoal] = useState<Goal | null>(null);
  const [checkIns, setCheckIns] = useState<CheckIn[]>([]);
  const [history, setHistory] = useState<AuditEvent[]>([]);
  const [notes, setNotes] = useState("");
  const [evidenceTitle, setEvidenceTitle] = useState("Sprint artifact");
  const [evidenceUrl, setEvidenceUrl] = useState("https://example.com/evidence");
  const [actuals, setActuals] = useState<Record<string, string>>({});
  const [error, setError] = useState("");

  async function load() {
    const g = await api.goal(params.id);
    setGoal(g);
    const snap: Record<string, string> = {};
    g.key_results.forEach((kr) => {
      snap[kr.key_result_id] = kr.actual == null ? "" : String(kr.actual);
    });
    setActuals(snap);
    const [cis, audits] = await Promise.all([
      api.checkIns({ goal_id: g.goal_id, limit: 50 }),
      api.auditForEntity("goal", g.goal_id),
    ]);
    setCheckIns(cis);
    setHistory(audits);
  }

  useEffect(() => {
    load().catch((e) => setError(e instanceof ApiError ? e.detail : "Failed to load"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.id]);

  async function submitCheckIn(e: FormEvent) {
    e.preventDefault();
    if (!goal) return;
    const snapshot: Record<string, number> = {};
    Object.entries(actuals).forEach(([k, v]) => {
      if (v !== "") snapshot[k] = Number(v);
    });
    try {
      await api.createCheckIn(goal.goal_id, {
        employee_employee_id: goal.employee_business_id,
        goal_goal_id: goal.goal_id,
        check_in_date: new Date().toISOString().slice(0, 10),
        notes,
        progress_snapshot: snapshot,
        evidence: [{ title: evidenceTitle, url: evidenceUrl, evidence_type: "url" }],
      });
      push("Check-in saved and progress recalculated", "success");
      await load();
    } catch (err) {
      push(err instanceof ApiError ? err.detail : "Check-in failed", "error");
    }
  }

  if (error) return <p className="text-rose-600">{error}</p>;
  if (!goal) return <p className="text-sm text-slate-500">Loading…</p>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">{goal.title}</h1>
        <p className="text-sm text-slate-500">
          {goal.goal_id} · {goal.employee_name} · cycle {goal.cycle_business_id} · v{goal.version}
        </p>
        <Badge tone={statusTone(goal.status)}>{goal.status}</Badge>
      </div>
      <div className="card p-4">
        <p className="text-sm text-slate-600">{goal.description}</p>
        <div className="mt-4">
          <ProgressBar value={goal.progress_percentage} />
          <p className="mt-2 text-sm">
            Weighted progress: <strong>{goal.progress_percentage.toFixed(1)}%</strong>
          </p>
          <p className="mt-1 text-xs text-slate-500">
            Each key result uses capped progress from baseline/actual/target (never dividing by zero). Goal progress is the
            weight-normalized average of valid KRs. Raw overachievement is stored separately from display-capped progress.
          </p>
        </div>
      </div>
      <div className="card p-4">
        <h2 className="mb-3 font-semibold">Key results</h2>
        {goal.key_results.map((kr) => (
          <div key={kr.id} className="mb-3 rounded-lg border border-slate-100 p-3 text-sm">
            <p className="font-medium">{kr.title}</p>
            <p className="text-xs text-slate-500">
              {kr.key_result_id} · {kr.metric_type} · baseline {kr.baseline} · target {kr.target} · actual {kr.actual ?? "—"} ·
              weight {kr.weight}
            </p>
            <ProgressBar value={kr.progress_percentage || 0} />
          </div>
        ))}
      </div>
      <form onSubmit={submitCheckIn} className="card space-y-3 p-4">
        <h2 className="font-semibold">Submit check-in with evidence</h2>
        {goal.key_results.map((kr) => (
          <label key={kr.id} className="block text-sm">
            Update actual for {kr.key_result_id}
            <input
              className="input mt-1"
              value={actuals[kr.key_result_id] || ""}
              onChange={(e) => setActuals({ ...actuals, [kr.key_result_id]: e.target.value })}
            />
          </label>
        ))}
        <textarea className="input" placeholder="Notes" value={notes} onChange={(e) => setNotes(e.target.value)} />
        <div className="grid gap-2 md:grid-cols-2">
          <input className="input" value={evidenceTitle} onChange={(e) => setEvidenceTitle(e.target.value)} placeholder="Evidence title" />
          <input className="input" value={evidenceUrl} onChange={(e) => setEvidenceUrl(e.target.value)} placeholder="Evidence URL" />
        </div>
        <button className="btn btn-primary">Save check-in</button>
      </form>
      <div className="card p-4">
        <h2 className="mb-3 font-semibold">Check-in history</h2>
        {checkIns.map((c) => (
          <div key={c.id} className="mb-2 text-sm">
            {c.check_in_date}: {c.notes || "No notes"} · evidence {c.evidence.length}
          </div>
        ))}
        {checkIns.length === 0 ? <p className="text-sm text-slate-500">No check-ins yet.</p> : null}
      </div>
      <div className="card p-4">
        <h2 className="mb-3 font-semibold">Goal versions / audit</h2>
        {history.map((h) => (
          <p key={h.id} className="text-xs text-slate-600">
            {h.action} · {h.reason} · {h.created_at}
          </p>
        ))}
      </div>
    </div>
  );
}

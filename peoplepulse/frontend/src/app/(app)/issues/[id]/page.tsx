"use client";

import { FormEvent, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { useToast } from "@/components/ui/Toast";
import { Badge, statusTone } from "@/components/ui/Badge";
import type { Issue } from "@/types";

export default function IssueDetailPage() {
  const params = useParams<{ id: string }>();
  const { push } = useToast();
  const [issue, setIssue] = useState<Issue | null>(null);
  const [notes, setNotes] = useState("");
  const [status, setStatus] = useState("resolved");
  const [error, setError] = useState("");

  useEffect(() => {
    api.issue(params.id).then(setIssue).catch((e) => setError(e instanceof ApiError ? e.detail : "Not found"));
  }, [params.id]);

  async function resolve(e: FormEvent) {
    e.preventDefault();
    if (!issue) return;
    if (!confirm("Update this exception status?")) return;
    try {
      const updated = await api.resolveIssue(issue.issue_id, { notes, resolution_status: status });
      setIssue(updated);
      push("Issue updated", "success");
    } catch (err) {
      push(err instanceof ApiError ? err.detail : "Update failed", "error");
    }
  }

  if (error) return <p className="text-rose-600">{error}</p>;
  if (!issue) return <p className="text-sm text-slate-500">Loading…</p>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">{issue.issue_id}</h1>
        <p className="text-sm text-slate-500">{issue.rule_id} · {issue.entity_type} {issue.entity_id}</p>
        <Badge tone={statusTone(issue.severity)}>{issue.severity}</Badge>
      </div>
      <div className="card space-y-2 p-4 text-sm">
        <p><strong>Violated rule:</strong> {issue.rule_id}</p>
        <p>{issue.explanation}</p>
        <p>Expected: {issue.expected_value || "—"}</p>
        <p>Actual: {issue.actual_value || "—"}</p>
        <p>Detected: {issue.detected_at}</p>
        <p>Status: {issue.resolution_status}</p>
      </div>
      <form onSubmit={resolve} className="card space-y-3 p-4">
        <select className="input" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="investigating">investigating</option>
          <option value="resolved">resolved</option>
          <option value="dismissed">dismissed</option>
        </select>
        <textarea className="input" value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Resolution notes" />
        <button className="btn btn-primary">Update resolution</button>
      </form>
    </div>
  );
}

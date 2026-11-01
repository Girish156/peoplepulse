"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Badge, statusTone } from "@/components/ui/Badge";
import { EmptyState, Skeleton } from "@/components/ui/EmptyState";
import type { Issue } from "@/types";

export default function IssuesPage() {
  const [rows, setRows] = useState<Issue[] | null>(null);
  const [issue_type, setType] = useState("");
  const [severity, setSeverity] = useState("");
  const [resolution_status, setStatus] = useState("");

  function load(e?: FormEvent) {
    e?.preventDefault();
    setRows(null);
    api.issues({ issue_type: issue_type || undefined, severity: severity || undefined, resolution_status: resolution_status || undefined, limit: 50 }).then(setRows);
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Exceptions</h1>
      <p className="text-sm text-slate-500">
        Detector output only. Ground-truth labels are never loaded by this screen or the API.
      </p>
      <form onSubmit={load} className="flex flex-wrap gap-2">
        <select className="input max-w-xs" value={issue_type} onChange={(e) => setType(e.target.value)}>
          <option value="">All types</option>
          <option value="goal_owner_mismatch">goal_owner_mismatch</option>
          <option value="progress_exceeds_scale">progress_exceeds_scale</option>
          <option value="reviewer_no_relationship">reviewer_no_relationship</option>
          <option value="closed_cycle_edit">closed_cycle_edit</option>
          <option value="untraceable_feedback">untraceable_feedback</option>
        </select>
        <select className="input max-w-xs" value={severity} onChange={(e) => setSeverity(e.target.value)}>
          <option value="">All severities</option>
          <option value="low">low</option>
          <option value="medium">medium</option>
          <option value="high">high</option>
          <option value="critical">critical</option>
        </select>
        <select className="input max-w-xs" value={resolution_status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All statuses</option>
          <option value="open">open</option>
          <option value="investigating">investigating</option>
          <option value="resolved">resolved</option>
          <option value="dismissed">dismissed</option>
        </select>
        <button className="btn btn-primary">Filter</button>
      </form>
      {!rows ? (
        <Skeleton className="h-48" />
      ) : rows.length === 0 ? (
        <EmptyState title="No exceptions" hint="Run detectors from this list after loading generated data." />
      ) : (
        <div className="card overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">Issue</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Entity</th>
                <th className="px-4 py-3">Severity</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((i) => (
                <tr key={i.id} className="border-t border-slate-100">
                  <td className="px-4 py-3">
                    <Link className="text-indigo-700" href={`/issues/${i.issue_id}`}>{i.issue_id}</Link>
                  </td>
                  <td className="px-4 py-3">{i.issue_type}</td>
                  <td className="px-4 py-3">{i.entity_type} {i.entity_id}</td>
                  <td className="px-4 py-3"><Badge tone={statusTone(i.severity)}>{i.severity}</Badge></td>
                  <td className="px-4 py-3"><Badge tone={statusTone(i.resolution_status)}>{i.resolution_status}</Badge></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

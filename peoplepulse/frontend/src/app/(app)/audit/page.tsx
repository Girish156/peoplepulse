"use client";

import { FormEvent, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { formatDateTime } from "@/lib/formatters";
import { EmptyState, Skeleton } from "@/components/ui/EmptyState";
import type { AuditEvent } from "@/types";

export default function AuditPage() {
  const [rows, setRows] = useState<AuditEvent[] | null>(null);
  const [entity_type, setType] = useState("");
  const [action, setAction] = useState("");

  function load(e?: FormEvent) {
    e?.preventDefault();
    setRows(null);
    api.audit({ entity_type: entity_type || undefined, action: action || undefined, limit: 50 }).then(setRows);
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Audit history</h1>
      <form onSubmit={load} className="flex flex-wrap gap-2">
        <input className="input max-w-xs" placeholder="entity type" value={entity_type} onChange={(e) => setType(e.target.value)} />
        <input className="input max-w-xs" placeholder="action" value={action} onChange={(e) => setAction(e.target.value)} />
        <button className="btn btn-primary">Filter</button>
      </form>
      {!rows ? (
        <Skeleton className="h-48" />
      ) : rows.length === 0 ? (
        <EmptyState title="No audit events" />
      ) : (
        <div className="space-y-3">
          {rows.map((e) => (
            <div key={e.id} className="card p-4 text-sm">
              <p className="font-medium">{e.action}</p>
              <p className="text-xs text-slate-500">
                {e.entity_type} {e.entity_id} · {e.actor_role || "system"} · {formatDateTime(e.created_at)}
              </p>
              <p className="mt-1 text-slate-600">{e.reason}</p>
              <pre className="mt-2 overflow-x-auto rounded bg-slate-50 p-2 text-xs">
                {JSON.stringify({ before: e.before_state, after: e.after_state }, null, 2)}
              </pre>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

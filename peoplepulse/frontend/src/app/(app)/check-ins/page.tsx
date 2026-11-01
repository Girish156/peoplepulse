"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { EmptyState, Skeleton } from "@/components/ui/EmptyState";
import type { CheckIn } from "@/types";

export default function CheckInsPage() {
  const [rows, setRows] = useState<CheckIn[] | null>(null);

  useEffect(() => {
    api.checkIns({ limit: 50 }).then(setRows);
  }, []);

  if (!rows) return <Skeleton className="h-64" />;
  if (rows.length === 0) return <EmptyState title="No check-ins" hint="Submit one from a goal detail page." />;

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Check-ins</h1>
      <div className="card overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">ID</th>
              <th className="px-4 py-3">Date</th>
              <th className="px-4 py-3">Employee</th>
              <th className="px-4 py-3">Goal</th>
              <th className="px-4 py-3">Notes</th>
              <th className="px-4 py-3">Evidence</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((c) => (
              <tr key={c.id} className="border-t border-slate-100">
                <td className="px-4 py-3 font-mono text-xs">{c.check_in_id}</td>
                <td className="px-4 py-3">{c.check_in_date}</td>
                <td className="px-4 py-3">{c.employee_name}</td>
                <td className="px-4 py-3">
                  <Link className="text-indigo-700" href={`/goals/${c.goal_id}`}>
                    {c.goal_title}
                  </Link>
                </td>
                <td className="px-4 py-3">{c.notes}</td>
                <td className="px-4 py-3">{c.evidence.map((e) => e.title).join(", ") || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

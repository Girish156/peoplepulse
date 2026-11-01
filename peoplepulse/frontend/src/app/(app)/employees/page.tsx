"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Badge, statusTone } from "@/components/ui/Badge";
import { EmptyState, Skeleton } from "@/components/ui/EmptyState";
import type { Employee } from "@/types";

export default function EmployeesPage() {
  const [rows, setRows] = useState<Employee[] | null>(null);
  const [search, setSearch] = useState("");
  const [department, setDepartment] = useState("");

  function load(e?: FormEvent) {
    e?.preventDefault();
    setRows(null);
    api.employees({ search, department, limit: 50 }).then(setRows);
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Employees</h1>
      <form onSubmit={load} className="flex flex-wrap gap-2">
        <input className="input max-w-xs" placeholder="Search name, ID, email" value={search} onChange={(e) => setSearch(e.target.value)} />
        <input className="input max-w-xs" placeholder="Department" value={department} onChange={(e) => setDepartment(e.target.value)} />
        <button className="btn btn-primary">Filter</button>
      </form>
      {!rows ? (
        <Skeleton className="h-64" />
      ) : rows.length === 0 ? (
        <EmptyState title="No employees found" hint="Load synthetic data from Admin / data quality, then refresh." />
      ) : (
        <div className="card overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-3">ID</th>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Department</th>
                <th className="px-4 py-3">Title</th>
                <th className="px-4 py-3">Manager</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((e) => (
                <tr key={e.id} className="border-t border-slate-100">
                  <td className="px-4 py-3 font-mono text-xs">
                    <Link className="text-indigo-700 hover:underline" href={`/employees/${e.employee_id}`}>
                      {e.employee_id}
                    </Link>
                  </td>
                  <td className="px-4 py-3">{e.name}</td>
                  <td className="px-4 py-3">{e.department}</td>
                  <td className="px-4 py-3">{e.job_title}</td>
                  <td className="px-4 py-3">{e.manager_name || "—"}</td>
                  <td className="px-4 py-3">
                    <Badge tone={statusTone(e.employment_status)}>{e.employment_status}</Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

"use client";

import { FormEvent, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { useToast } from "@/components/ui/Toast";
import type { AdminJob } from "@/types";

export default function SettingsPage() {
  const { push } = useToast();
  const [mode, setMode] = useState("small");
  const [seed, setSeed] = useState("20261022");
  const [job, setJob] = useState<AdminJob | null>(null);
  const [report, setReport] = useState<Record<string, unknown> | null>(null);
  const [polling, setPolling] = useState(false);

  async function poll(jobId: string) {
    setPolling(true);
    for (let i = 0; i < 40; i++) {
      const current = await api.job(jobId);
      setJob(current);
      if (current.status === "completed" || current.status === "failed") {
        setPolling(false);
        return;
      }
      await new Promise((r) => setTimeout(r, 1500));
    }
    setPolling(false);
  }

  async function generate(e: FormEvent) {
    e.preventDefault();
    try {
      const created = await api.generateData(mode, Number(seed));
      setJob(created);
      push(`Job ${created.job_id} queued`, "info");
      await poll(created.job_id);
    } catch (err) {
      push(err instanceof ApiError ? err.detail : "Only admin can generate data", "error");
    }
  }

  async function loadReport() {
    try {
      const data = await api.validationReport();
      setReport(data);
    } catch (err) {
      push(err instanceof ApiError ? err.detail : "Unable to load report", "error");
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Admin / data quality</h1>
        <p className="text-sm text-slate-500">
          Long-running generation runs as a background job. Ground truth is never returned by these endpoints.
        </p>
      </div>
      <form onSubmit={generate} className="card grid gap-3 p-4 md:grid-cols-3">
        <select className="input" value={mode} onChange={(e) => setMode(e.target.value)}>
          <option value="small">small</option>
          <option value="full">full</option>
        </select>
        <input className="input" value={seed} onChange={(e) => setSeed(e.target.value)} />
        <button className="btn btn-primary" disabled={polling}>
          {polling ? "Job running…" : "Generate data"}
        </button>
      </form>
      {job ? (
        <div className="card p-4 text-sm">
          <p>Job {job.job_id}: {job.status}</p>
          {job.error ? <pre className="mt-2 text-rose-600">{job.error}</pre> : null}
          {job.output ? <pre className="mt-2 max-h-48 overflow-auto bg-slate-50 p-2 text-xs">{job.output}</pre> : null}
        </div>
      ) : null}
      <button className="btn btn-secondary" onClick={loadReport}>Load validation report</button>
      {report ? (
        <pre className="card max-h-[480px] overflow-auto p-4 text-xs">{JSON.stringify(report, null, 2)}</pre>
      ) : null}
    </div>
  );
}

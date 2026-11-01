import { clsx } from "@/lib/formatters";

const tones: Record<string, string> = {
  success: "bg-emerald-50 text-emerald-700 ring-emerald-100",
  warning: "bg-amber-50 text-amber-700 ring-amber-100",
  danger: "bg-rose-50 text-rose-700 ring-rose-100",
  info: "bg-sky-50 text-sky-700 ring-sky-100",
  neutral: "bg-slate-100 text-slate-700 ring-slate-200",
  purple: "bg-indigo-50 text-indigo-700 ring-indigo-100",
};

export function Badge({ children, tone = "neutral" }: { children: React.ReactNode; tone?: keyof typeof tones | string }) {
  return (
    <span className={clsx("inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1", tones[tone] || tones.neutral)}>
      {children}
    </span>
  );
}

export function statusTone(status?: string): string {
  const s = (status || "").toLowerCase();
  if (["active", "submitted", "completed", "approved", "resolved"].includes(s)) return "success";
  if (["pending", "draft", "open", "investigating", "in_progress"].includes(s)) return "warning";
  if (["closed", "terminated", "cancelled", "dismissed", "critical", "high"].includes(s)) return "danger";
  if (["archived"].includes(s)) return "neutral";
  return "info";
}

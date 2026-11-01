"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  Activity,
  AlertTriangle,
  ClipboardCheck,
  Flag,
  LayoutDashboard,
  LogOut,
  MessageSquare,
  ScrollText,
  Settings,
  Target,
  Users,
} from "lucide-react";
import { clearSession, getSession } from "@/lib/auth";
import { clsx } from "@/lib/formatters";
import { ToastProvider } from "@/components/ui/Toast";
import type { AuthUser } from "@/types";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/employees", label: "Employees", icon: Users },
  { href: "/goals", label: "Goals", icon: Target },
  { href: "/check-ins", label: "Check-ins", icon: ClipboardCheck },
  { href: "/feedback", label: "Feedback", icon: MessageSquare },
  { href: "/reviews", label: "Reviews", icon: Flag },
  { href: "/development-plans", label: "Development", icon: Activity },
  { href: "/issues", label: "Exceptions", icon: AlertTriangle },
  { href: "/audit", label: "Audit history", icon: ScrollText },
  { href: "/settings", label: "Admin / data quality", icon: Settings },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    const session = getSession();
    if (!session) {
      router.replace("/login");
      return;
    }
    setUser(session);
  }, [router]);

  if (!user) {
    return <div className="grid min-h-screen place-items-center text-sm text-slate-500">Loading session…</div>;
  }

  return (
    <ToastProvider>
      <div className="flex min-h-screen">
        <aside className="hidden w-64 shrink-0 border-r border-slate-200 bg-white md:flex md:flex-col">
          <div className="border-b border-slate-100 px-5 py-5">
            <p className="text-lg font-semibold tracking-tight text-indigo-700">PeoplePulse</p>
            <p className="text-xs text-slate-500">Evidence-based reviews</p>
          </div>
          <nav className="flex-1 space-y-1 p-3">
            {NAV.map((item) => {
              const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={clsx(
                    "flex items-center gap-2 rounded-lg px-3 py-2 text-sm",
                    active ? "bg-indigo-50 font-medium text-indigo-700" : "text-slate-600 hover:bg-slate-50"
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
          <div className="border-t border-slate-100 p-4 text-xs text-slate-500">
            Demo auth only — not production security.
          </div>
        </aside>
        <div className="flex min-w-0 flex-1 flex-col">
          <header className="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3 md:px-8">
            <div className="md:hidden text-sm font-semibold text-indigo-700">PeoplePulse</div>
            <div className="ml-auto flex items-center gap-3 text-sm">
              <div className="text-right">
                <p className="font-medium text-slate-800">{user.name}</p>
                <p className="text-xs capitalize text-slate-500">{user.role.replace("_", " ")}</p>
              </div>
              <button
                className="btn btn-secondary"
                onClick={() => {
                  clearSession();
                  router.replace("/login");
                }}
              >
                <LogOut className="h-4 w-4" />
                Sign out
              </button>
            </div>
          </header>
          <main className="flex-1 px-4 py-6 md:px-8">{children}</main>
        </div>
      </div>
    </ToastProvider>
  );
}

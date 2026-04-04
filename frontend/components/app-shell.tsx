"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { getOfflineQueueSize } from "../lib/api-client";
import { UserRole } from "../types/api";

import { useAuth } from "./auth-provider";
import { useOffline } from "../hooks/use-offline";

const NAV_ITEMS: Array<{ href: string; label: string; roles: UserRole[] }> = [
  { href: "/dashboard", label: "Dashboard", roles: ["Super Admin", "Manager", "Pharmacist", "Staff"] },
  { href: "/inventory", label: "Inventory", roles: ["Super Admin", "Manager", "Pharmacist", "Staff"] },
  { href: "/billing", label: "Billing", roles: ["Super Admin", "Pharmacist"] },
  { href: "/analytics", label: "Analytics", roles: ["Super Admin", "Manager"] },
  { href: "/ai", label: "AI Insights", roles: ["Super Admin", "Manager", "Pharmacist"] },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isOffline = useOffline();
  const { auth, logout } = useAuth();

  if (!auth) {
    return <>{children}</>;
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="sticky top-0 z-20 border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2 p-3">
          <div>
            <p className="text-sm font-semibold text-slate-900">Pharma Ops</p>
            <p className="text-xs text-slate-500">Role: {auth.user.role}</p>
          </div>
          <nav className="flex flex-wrap gap-2 text-sm">
            {NAV_ITEMS.filter((item) => item.roles.includes(auth.user.role)).map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`rounded px-2 py-1 ${pathname === item.href ? "bg-teal-600 text-white" : "bg-slate-100 text-slate-700"}`}
              >
                {item.label}
              </Link>
            ))}
          </nav>
          <button
            onClick={logout}
            className="rounded border border-slate-300 px-3 py-1 text-sm text-slate-700"
            type="button"
          >
            Logout
          </button>
        </div>
      </header>
      {(isOffline || getOfflineQueueSize() > 0) && (
        <div className="border-b border-amber-300 bg-amber-50 px-4 py-2 text-xs text-amber-800">
          {isOffline ? "Offline mode enabled. New write actions can be queued locally." : "You have queued offline actions pending sync."}
        </div>
      )}
      <main className="mx-auto max-w-6xl p-4">{children}</main>
    </div>
  );
}

"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { roleCanAccess } from "../lib/auth";
import { UserRole } from "../types/api";

import { useAuth } from "./auth-provider";

interface ProtectedPageProps {
  allowedRoles?: UserRole[];
  children: React.ReactNode;
}

export function ProtectedPage({ allowedRoles, children }: ProtectedPageProps) {
  const router = useRouter();
  const { auth, loading } = useAuth();

  useEffect(() => {
    if (loading) {
      return;
    }

    if (!auth) {
      router.replace("/login");
      return;
    }

    if (allowedRoles && !roleCanAccess(auth.user.role, allowedRoles)) {
      router.replace("/dashboard");
    }
  }, [auth, loading, allowedRoles, router]);

  if (loading || !auth) {
    return <div className="p-6 text-sm text-slate-600">Loading session...</div>;
  }

  if (allowedRoles && !roleCanAccess(auth.user.role, allowedRoles)) {
    return <div className="p-6 text-sm text-slate-600">Checking permissions...</div>;
  }

  return <>{children}</>;
}

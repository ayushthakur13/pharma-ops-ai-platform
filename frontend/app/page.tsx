"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "../components/auth-provider";

export default function HomePage() {
  const router = useRouter();
  const { auth, loading } = useAuth();

  useEffect(() => {
    if (loading) {
      return;
    }
    router.replace(auth ? "/dashboard" : "/login");
  }, [auth, loading, router]);

  return <div className="p-6 text-sm text-slate-600">Routing...</div>;
}

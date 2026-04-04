"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";

import { apiRequest, ApiClientError } from "../lib/api-client";
import { AuthState, clearAuthState, loadAuthState, saveAuthState } from "../lib/auth";
import { CurrentUser, LoginResponse, UserRole } from "../types/api";

interface AuthContextValue {
  auth: AuthState | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [auth, setAuth] = useState<AuthState | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initial = loadAuthState();
    if (initial) {
      setAuth(initial);
    }
    setLoading(false);
  }, []);

  const login = async (email: string, password: string) => {
    const response = (await apiRequest<LoginResponse>("/api/auth/login", {
      method: "POST",
      body: { email, password },
    })) as LoginResponse;

    const me = (await apiRequest<CurrentUser>("/api/auth/me", {
      token: response.access_token,
    })) as CurrentUser;

    const nextState: AuthState = {
      token: response.access_token,
      user: {
        id: me.id,
        email: me.email,
        role: me.role as UserRole,
      },
    };

    saveAuthState(nextState);
    setAuth(nextState);
  };

  const logout = () => {
    clearAuthState();
    setAuth(null);
  };

  const value = useMemo(
    () => ({ auth, loading, login, logout }),
    [auth, loading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return ctx;
}

export function useApiErrorMessage(error: unknown): string {
  if (error instanceof ApiClientError) {
    if (error.status === 401) {
      return "Your session is invalid or expired. Please login again.";
    }
    if (error.status === 403) {
      return "You do not have permission to perform this action.";
    }
    if (error.status === 409) {
      return "This operation conflicts with current stock or existing data.";
    }
    return error.details || error.message;
  }
  return "Unexpected error. Please try again.";
}

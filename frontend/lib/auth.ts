import { CurrentUser, LoginResponse, UserRole } from "../types/api";

const AUTH_KEY = "pharma_ops_auth";

export interface AuthState {
  token: string;
  user: LoginResponse["user"] | CurrentUser;
}

export const roleCanAccess = (role: UserRole, allowed: UserRole[]): boolean => allowed.includes(role);

export function loadAuthState(): AuthState | null {
  if (typeof window === "undefined") {
    return null;
  }
  const raw = window.localStorage.getItem(AUTH_KEY);
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw) as AuthState;
  } catch {
    window.localStorage.removeItem(AUTH_KEY);
    return null;
  }
}

export function saveAuthState(state: AuthState): void {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(AUTH_KEY, JSON.stringify(state));
}

export function clearAuthState(): void {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.removeItem(AUTH_KEY);
}

import { ApiError, OfflineQueuedResult } from "../types/api";

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";
const OFFLINE_QUEUE_KEY = "pharma_ops_offline_queue";

export class ApiClientError extends Error {
  status: number;
  details?: string;

  constructor(message: string, status: number, details?: string) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.details = details;
  }
}

interface ApiRequestOptions {
  method?: "GET" | "POST";
  token?: string;
  body?: Record<string, unknown>;
  queueOnOffline?: boolean;
}

function queueOfflineAction(path: string, method: string, body?: Record<string, unknown>): OfflineQueuedResult {
  const queuedAt = new Date().toISOString();
  if (typeof window !== "undefined") {
    const existing = window.localStorage.getItem(OFFLINE_QUEUE_KEY);
    const parsed = existing ? (JSON.parse(existing) as unknown[]) : [];
    parsed.push({ path, method, body, queued_at: queuedAt });
    window.localStorage.setItem(OFFLINE_QUEUE_KEY, JSON.stringify(parsed));
  }
  return { offline_queued: true, queued_at: queuedAt };
}

export function getOfflineQueueSize(): number {
  if (typeof window === "undefined") {
    return 0;
  }
  const existing = window.localStorage.getItem(OFFLINE_QUEUE_KEY);
  if (!existing) {
    return 0;
  }
  try {
    return (JSON.parse(existing) as unknown[]).length;
  } catch {
    return 0;
  }
}

export async function apiRequest<T>(path: string, options: ApiRequestOptions = {}): Promise<T | OfflineQueuedResult> {
  const method = options.method || "GET";

  try {
    const response = await fetch(`${BASE_URL}${path}`, {
      method,
      headers: {
        "Content-Type": "application/json",
        ...(options.token ? { Authorization: `Bearer ${options.token}` } : {}),
      },
      body: options.body ? JSON.stringify(options.body) : undefined,
      cache: "no-store",
    });

    if (response.status === 204) {
      return {} as T;
    }

    const data = (await response.json().catch(() => ({}))) as ApiError | T;

    if (!response.ok) {
      const details = (data as ApiError).detail || (data as ApiError).message || "Request failed";
      throw new ApiClientError(details, response.status, details);
    }

    return data as T;
  } catch (error) {
    if (options.queueOnOffline && error instanceof TypeError) {
      return queueOfflineAction(path, method, options.body);
    }
    throw error;
  }
}

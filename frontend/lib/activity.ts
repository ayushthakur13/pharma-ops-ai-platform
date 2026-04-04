const ACTIVITY_KEY = "pharma_ops_recent_activity";

export interface ActivityItem {
  id: number;
  type: "prescription" | "transaction";
  note: string;
  created_at: string;
}

export function loadActivity(): ActivityItem[] {
  if (typeof window === "undefined") {
    return [];
  }
  const raw = window.localStorage.getItem(ACTIVITY_KEY);
  if (!raw) {
    return [];
  }
  try {
    return JSON.parse(raw) as ActivityItem[];
  } catch {
    return [];
  }
}

export function pushActivity(item: ActivityItem): void {
  if (typeof window === "undefined") {
    return;
  }
  const all = loadActivity();
  all.unshift(item);
  window.localStorage.setItem(ACTIVITY_KEY, JSON.stringify(all.slice(0, 20)));
}

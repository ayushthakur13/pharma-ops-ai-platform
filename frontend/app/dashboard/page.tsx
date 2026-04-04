"use client";

import { useEffect, useMemo, useState } from "react";

import { ProtectedPage } from "../../components/protected-page";
import { useApiErrorMessage, useAuth } from "../../components/auth-provider";
import { apiRequest, ApiClientError } from "../../lib/api-client";
import { loadActivity } from "../../lib/activity";
import { AnomalyResponse, DemandTrendsResponse, StockItem, StorePerformanceResponse } from "../../types/api";

const ALL_ROLES = ["Super Admin", "Manager", "Pharmacist", "Staff"] as const;

export default function DashboardPage() {
  const { auth } = useAuth();
  const [storeId, setStoreId] = useState(1);
  const [loading, setLoading] = useState(false);
  const [stockAlerts, setStockAlerts] = useState(0);
  const [recentTransactions, setRecentTransactions] = useState(0);
  const [anomalyCount, setAnomalyCount] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [managerSummary, setManagerSummary] = useState<string>("");
  const recentActivity = useMemo(() => loadActivity().slice(0, 5), []);

  useEffect(() => {
    void refreshMetrics();
  }, []);

  const refreshMetrics = async () => {
    if (!auth) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const stock = (await apiRequest<StockItem[]>(`/api/inventory/stock/${storeId}`, {
        token: auth.token,
      })) as StockItem[];
      setStockAlerts(stock.filter((item) => item.quantity_on_hand <= item.reorder_level).length);

      try {
        const anomalies = (await apiRequest<AnomalyResponse>("/api/ai/anomalies/detect", {
          method: "POST",
          token: auth.token,
          body: {
            store_id: storeId,
            date_range: { from: "2026-04-01", to: "2026-04-04" },
          },
        })) as AnomalyResponse;
        setAnomalyCount(anomalies.anomalies.length);
      } catch (aiErr) {
        if (!(aiErr instanceof ApiClientError && aiErr.status === 403)) {
          throw aiErr;
        }
        setAnomalyCount(0);
      }

      if (auth.user.role === "Manager" || auth.user.role === "Super Admin") {
        const trends = (await apiRequest<DemandTrendsResponse>(`/api/analytics/demand-trends?store_id=${storeId}`, {
          token: auth.token,
        })) as DemandTrendsResponse;

        const performance = (await apiRequest<StorePerformanceResponse>("/api/analytics/store-performance", {
          token: auth.token,
        })) as StorePerformanceResponse;

        setRecentTransactions(trends.trend.reduce((acc, point) => acc + point.transactions, 0));
        setManagerSummary(`Stores tracked: ${performance.stores.length}`);
      } else {
        setRecentTransactions(recentActivity.filter((item) => item.type === "transaction").length);
      }
    } catch (err) {
      setError(useApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <ProtectedPage allowedRoles={[...ALL_ROLES]}>
      <div className="space-y-4">
        <div className="flex flex-wrap items-end gap-3">
          <div>
            <label className="block text-sm font-medium text-slate-700">Store ID</label>
            <input
              type="number"
              value={storeId}
              onChange={(e) => setStoreId(Number(e.target.value))}
              className="mt-1 w-28 border px-2 py-1"
              min={1}
            />
          </div>
          <button
            type="button"
            onClick={() => void refreshMetrics()}
            className="rounded bg-teal-600 px-3 py-2 text-sm text-white"
            disabled={loading}
          >
            {loading ? "Refreshing..." : "Refresh"}
          </button>
        </div>

        {error && <p className="rounded bg-red-50 p-2 text-sm text-red-700">{error}</p>}

        <div className="grid gap-3 sm:grid-cols-3">
          <Card title="Stock Alerts" value={String(stockAlerts)} />
          <Card title="Recent Transactions" value={String(recentTransactions)} />
          <Card title="Anomalies" value={String(anomalyCount)} />
        </div>

        <div className="rounded border border-slate-200 bg-white p-3">
          <h2 className="text-sm font-medium text-slate-800">Recent Actions</h2>
          <p className="mt-1 text-xs text-slate-500">System logs preview from recent UI operations in this browser session.</p>
          <ul className="mt-2 space-y-1 text-sm text-slate-600">
            {recentActivity.map((item) => (
              <li key={`${item.type}-${item.id}-${item.created_at}`}>
                [{item.type}] {item.note}
              </li>
            ))}
            {recentActivity.length === 0 && <li>No recent actions captured yet.</li>}
          </ul>
        </div>

        {(auth?.user.role === "Manager" || auth?.user.role === "Super Admin") && (
          <div className="rounded border border-slate-200 bg-white p-3 text-sm text-slate-700">
            <h2 className="font-medium">Manager Analytics Preview</h2>
            <p className="mt-1">{managerSummary || "Refresh to load analytics preview."}</p>
          </div>
        )}

        {auth?.user.role === "Pharmacist" && (
          <div className="rounded border border-slate-200 bg-white p-3 text-xs text-slate-500">
            Full backend audit logs are captured server-side and can be surfaced via dedicated admin reporting views.
          </div>
        )}
      </div>
    </ProtectedPage>
  );
}

function Card({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded border border-slate-200 bg-white p-3">
      <p className="text-xs text-slate-500">{title}</p>
      <p className="mt-1 text-2xl font-semibold text-slate-900">{value}</p>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";

import { ProtectedPage } from "../../components/protected-page";
import { useApiErrorMessage, useAuth } from "../../components/auth-provider";
import { apiRequest } from "../../lib/api-client";
import { DemandTrendsResponse, StockAgingResponse, StorePerformanceResponse, UserRole } from "../../types/api";

const ANALYTICS_ROLES: UserRole[] = ["Super Admin", "Manager"];

export default function AnalyticsPage() {
  const { auth } = useAuth();
  const [storeId, setStoreId] = useState(1);
  const [stockAging, setStockAging] = useState<StockAgingResponse | null>(null);
  const [demandTrends, setDemandTrends] = useState<DemandTrendsResponse | null>(null);
  const [storePerformance, setStorePerformance] = useState<StorePerformanceResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const loadAnalytics = async () => {
    if (!auth) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const [aging, trends, performance] = await Promise.all([
        apiRequest<StockAgingResponse>(`/api/analytics/stock-aging?store_id=${storeId}`, { token: auth.token }) as Promise<StockAgingResponse>,
        apiRequest<DemandTrendsResponse>(`/api/analytics/demand-trends?store_id=${storeId}`, { token: auth.token }) as Promise<DemandTrendsResponse>,
        apiRequest<StorePerformanceResponse>("/api/analytics/store-performance", { token: auth.token }) as Promise<StorePerformanceResponse>,
      ]);

      setStockAging(aging);
      setDemandTrends(trends);
      setStorePerformance(performance);
    } catch (err) {
      setError(useApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (auth) {
      void loadAnalytics();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [auth]);

  const stockBuckets = stockAging?.aging_buckets ?? [];
  const trendPoints = demandTrends?.trend ?? [];
  const stores = storePerformance?.stores ?? [];

  const maxAgingCount = Math.max(1, ...stockBuckets.map((bucket) => bucket.count));
  const maxTrendCount = Math.max(1, ...trendPoints.map((point) => point.transactions));

  const agingLead = stockBuckets.reduce<StockAgingResponse["aging_buckets"][number] | undefined>(
    (currentLead, candidate) => (!currentLead || candidate.count > currentLead.count ? candidate : currentLead),
    undefined,
  );
  const trendLead = trendPoints.reduce<DemandTrendsResponse["trend"][number] | undefined>(
    (currentLead, candidate) => (!currentLead || candidate.transactions > currentLead.transactions ? candidate : currentLead),
    undefined,
  );
  const totalTransactions = trendPoints.reduce((sum, point) => sum + point.transactions, 0);
  const averageStockOutRate = stores.length ? stores.reduce((sum, item) => sum + item.stock_out_rate, 0) / stores.length : 0;
  const topStore = stores.reduce<StorePerformanceResponse["stores"][number] | undefined>(
    (currentLead, candidate) => (!currentLead || candidate.stock_out_rate > currentLead.stock_out_rate ? candidate : currentLead),
    undefined,
  );
  const emptyState = stockBuckets.length === 0 && trendPoints.length === 0 && stores.length === 0;

  const insightCards = [
    {
      label: "Highest aging bucket",
      value: agingLead ? `${agingLead.range} days` : "No data",
      subtext: agingLead ? `${agingLead.count} items in this band` : "Load analytics to evaluate expiry exposure.",
    },
    {
      label: "Peak demand day",
      value: trendLead?.date || "No data",
      subtext: trendLead ? `${trendLead.transactions} transactions` : "Load demand trends to spot peaks.",
    },
    {
      label: "Avg stock-out rate",
      value: `${(averageStockOutRate * 100).toFixed(1)}%`,
      subtext: topStore ? `Highest-risk store: ${topStore.store_id}` : "Load store performance for comparison.",
    },
  ];

  return (
    <ProtectedPage allowedRoles={ANALYTICS_ROLES}>
      <div className="space-y-5">
        <h1 className="text-lg font-semibold text-slate-900">Analytics</h1>

        <div className="grid gap-3 rounded border border-slate-200 bg-white p-3 sm:grid-cols-3">
          <label className="text-sm text-slate-700">
            Store ID
            <input
              type="number"
              min={1}
              value={storeId}
              onChange={(e) => setStoreId(Number(e.target.value))}
              className="mt-1 w-full border px-2 py-1"
            />
          </label>
          <div className="flex items-end sm:col-span-2">
            <button
              type="button"
              onClick={() => void loadAnalytics()}
              className="rounded bg-teal-600 px-3 py-2 text-sm text-white"
              disabled={loading}
            >
              {loading ? "Loading..." : "Refresh"}
            </button>
          </div>
        </div>

        {error && <p className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>}

        <section className="grid gap-3 md:grid-cols-3">
          {insightCards.map((card) => (
            <div key={card.label} className="rounded border border-slate-200 bg-white p-3">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{card.label}</p>
              <p className="mt-1 text-2xl font-semibold text-slate-900">{card.value}</p>
              <p className="mt-1 text-sm text-slate-600">{card.subtext}</p>
            </div>
          ))}
        </section>

        <section className="grid gap-4 lg:grid-cols-2">
          <article className="rounded border border-slate-200 bg-white p-3">
            <div className="flex items-center justify-between gap-2">
              <div>
                <h2 className="font-medium text-slate-800">Stock Aging</h2>
                <p className="text-xs text-slate-500">Items approaching expiry by day bucket.</p>
              </div>
              <span className="rounded bg-teal-50 px-2 py-0.5 text-xs text-teal-700">
                {stockAging ? `${stockBuckets.length} buckets` : "Pending"}
              </span>
            </div>

            <div className="mt-3 space-y-3">
              {stockBuckets.map((bucket) => {
                const width = Math.max(8, Math.round((bucket.count / maxAgingCount) * 100));
                return (
                  <div key={bucket.range}>
                    <div className="mb-1 flex items-center justify-between text-xs text-slate-500">
                      <span>{bucket.range} days</span>
                      <span className="font-medium text-slate-700">{bucket.count} items</span>
                    </div>
                    <div className="h-3 w-full rounded-full bg-slate-100">
                      <div className="h-3 rounded-full bg-gradient-to-r from-amber-400 to-rose-500" style={{ width: `${width}%` }} />
                    </div>
                  </div>
                );
              })}
              {emptyState && <p className="text-sm text-slate-500">Load analytics to view stock aging.</p>}
            </div>
          </article>

          <article className="rounded border border-slate-200 bg-white p-3">
            <div className="flex items-center justify-between gap-2">
              <div>
                <h2 className="font-medium text-slate-800">Demand Trends</h2>
                <p className="text-xs text-slate-500">Transaction volume over the selected period.</p>
              </div>
              <span className="rounded bg-indigo-50 px-2 py-0.5 text-xs text-indigo-700">
                {demandTrends ? `${totalTransactions} txns total` : "Pending"}
              </span>
            </div>

            <div className="mt-3 space-y-3">
              {trendPoints.map((point) => {
                const width = Math.max(8, Math.round((point.transactions / maxTrendCount) * 100));
                return (
                  <div key={point.date}>
                    <div className="mb-1 flex items-center justify-between text-xs text-slate-500">
                      <span>{point.date}</span>
                      <span className="font-medium text-slate-700">{point.transactions} transactions</span>
                    </div>
                    <div className="h-3 w-full rounded-full bg-slate-100">
                      <div className="h-3 rounded-full bg-gradient-to-r from-indigo-400 to-sky-500" style={{ width: `${width}%` }} />
                    </div>
                  </div>
                );
              })}
              {emptyState && <p className="text-sm text-slate-500">Load analytics to view demand trends.</p>}
            </div>
          </article>
        </section>

        <section className="rounded border border-slate-200 bg-white p-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h2 className="font-medium text-slate-800">Store Performance</h2>
              <p className="text-xs text-slate-500">Compare stock-out rates, transactions, and revenue by store.</p>
            </div>
            <span className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
              {storePerformance ? `${stores.length} stores` : "Pending"}
            </span>
          </div>

          <div className="mt-3 overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
                  <th className="py-2 pr-4">Store</th>
                  <th className="py-2 pr-4">Stock-out</th>
                  <th className="py-2 pr-4">Transactions</th>
                  <th className="py-2 pr-4">Revenue</th>
                  <th className="py-2 pr-4">Risk</th>
                </tr>
              </thead>
              <tbody>
                {stores.map((item) => {
                  const riskWidth = Math.max(8, Math.round(item.stock_out_rate * 100));
                  return (
                    <tr key={item.store_id} className="border-b border-slate-100 last:border-0">
                      <td className="py-3 pr-4 font-medium text-slate-900">Store {item.store_id}</td>
                      <td className="py-3 pr-4 text-slate-600">{(item.stock_out_rate * 100).toFixed(1)}%</td>
                      <td className="py-3 pr-4 text-slate-600">{item.transaction_count}</td>
                      <td className="py-3 pr-4 text-slate-600">{item.revenue}</td>
                      <td className="py-3 pr-4">
                        <div className="h-2 w-24 rounded-full bg-slate-100">
                          <div
                            className={`h-2 rounded-full ${item.stock_out_rate > 0.2 ? "bg-rose-500" : item.stock_out_rate > 0.1 ? "bg-amber-500" : "bg-emerald-500"}`}
                            style={{ width: `${riskWidth}%` }}
                          />
                        </div>
                      </td>
                    </tr>
                  );
                })}
                {emptyState && (
                  <tr>
                    <td className="py-4 text-slate-500" colSpan={5}>
                      Load analytics to view store performance.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </ProtectedPage>
  );
}
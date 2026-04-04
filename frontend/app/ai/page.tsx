"use client";

import { FormEvent, useState } from "react";

import { ProtectedPage } from "../../components/protected-page";
import { useApiErrorMessage, useAuth } from "../../components/auth-provider";
import { apiRequest } from "../../lib/api-client";
import { AIQueryResponse, AnomalyResponse, ReplenishmentResponse } from "../../types/api";

const AI_ROLES = ["Super Admin", "Manager", "Pharmacist"] as const;

export default function AIPage() {
  const { auth } = useAuth();
  const [storeId, setStoreId] = useState(1);
  const [productId, setProductId] = useState(1);
  const [question, setQuestion] = useState("Give me store performance summary");

  const [replenishment, setReplenishment] = useState<ReplenishmentResponse | null>(null);
  const [anomalies, setAnomalies] = useState<AnomalyResponse | null>(null);
  const [aiQuery, setAiQuery] = useState<AIQueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchReplenishment = async () => {
    if (!auth) {
      return;
    }
    setError(null);
    try {
      const response = (await apiRequest<ReplenishmentResponse>("/api/ai/recommendations/replenishment", {
        method: "POST",
        token: auth.token,
        body: { store_id: storeId, product_id: productId },
      })) as ReplenishmentResponse;
      setReplenishment(response);
    } catch (err) {
      setError(useApiErrorMessage(err));
    }
  };

  const fetchAnomalies = async () => {
    if (!auth) {
      return;
    }
    setError(null);
    try {
      const response = (await apiRequest<AnomalyResponse>("/api/ai/anomalies/detect", {
        method: "POST",
        token: auth.token,
        body: {
          store_id: storeId,
          date_range: { from: "2026-04-01", to: "2026-04-04" },
        },
      })) as AnomalyResponse;
      setAnomalies(response);
    } catch (err) {
      setError(useApiErrorMessage(err));
    }
  };

  const submitQuery = async (event: FormEvent) => {
    event.preventDefault();
    if (!auth) {
      return;
    }
    setError(null);
    try {
      const response = (await apiRequest<AIQueryResponse>("/api/ai/query", {
        method: "POST",
        token: auth.token,
        body: {
          question,
          store_id: storeId,
        },
      })) as AIQueryResponse;
      setAiQuery(response);
    } catch (err) {
      setError(useApiErrorMessage(err));
    }
  };

  return (
    <ProtectedPage allowedRoles={[...AI_ROLES]}>
      <div className="space-y-4">
        <h1 className="text-lg font-semibold text-slate-900">AI Insights</h1>

        <div className="grid gap-3 rounded border border-slate-200 bg-white p-3 sm:grid-cols-2">
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
          <label className="text-sm text-slate-700">
            Product ID
            <input
              type="number"
              min={1}
              value={productId}
              onChange={(e) => setProductId(Number(e.target.value))}
              className="mt-1 w-full border px-2 py-1"
            />
          </label>
          <button className="rounded bg-teal-600 px-3 py-2 text-sm text-white" type="button" onClick={() => void fetchReplenishment()}>
            Get Replenishment
          </button>
          <button className="rounded bg-slate-900 px-3 py-2 text-sm text-white" type="button" onClick={() => void fetchAnomalies()}>
            Detect Anomalies
          </button>
        </div>

        <form onSubmit={submitQuery} className="rounded border border-slate-200 bg-white p-3">
          <label className="block text-sm text-slate-700">
            Ask Operational Question
            <input
              className="mt-1 w-full border px-2 py-1 text-sm"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              minLength={3}
              required
            />
          </label>
          <button className="mt-3 rounded bg-indigo-600 px-3 py-2 text-sm text-white" type="submit">
            Run Query
          </button>
        </form>

        {error && <p className="rounded bg-red-50 p-2 text-sm text-red-700">{error}</p>}

        <section className="rounded border border-slate-200 bg-white p-3 text-sm">
          <h2 className="font-medium text-slate-800">Replenishment Recommendations</h2>
          <ul className="mt-2 space-y-1 text-slate-600">
            {replenishment?.recommendations.map((item, idx) => (
              <li key={`${item.product_id}-${idx}`}>
                Product {item.product_id}: order {item.suggested_order_quantity} | explanation: {item.reason} | source: {item.source}
              </li>
            ))}
            {!replenishment && <li>No recommendation loaded yet.</li>}
          </ul>
        </section>

        <section className="rounded border border-slate-200 bg-white p-3 text-sm">
          <h2 className="font-medium text-slate-800">Anomaly Detection</h2>
          <p className="text-xs text-slate-500">Source: {anomalies?.source || "n/a"}</p>
          <ul className="mt-2 space-y-1 text-slate-600">
            {anomalies?.anomalies.map((item, idx) => (
              <li key={`${item.type}-${idx}`}>
                {item.type} ({item.severity}) - explanation: {item.explanation} - confidence {item.confidence}
              </li>
            ))}
            {!anomalies && <li>No anomaly data loaded yet.</li>}
          </ul>
        </section>

        <section className="rounded border border-slate-200 bg-white p-3 text-sm">
          <h2 className="font-medium text-slate-800">Conversational Insight</h2>
          <p className="text-slate-700">{aiQuery?.answer || "No query response yet."}</p>
          <p className="mt-1 text-xs text-slate-500">Intent: {aiQuery?.intent || "n/a"} | Source: {aiQuery?.source || "n/a"}</p>
          <p className="mt-2 text-xs text-amber-700">AI output is assistive. Always validate against operational policy.</p>
        </section>
      </div>
    </ProtectedPage>
  );
}

"use client";

import { FormEvent, useState } from "react";

import { useApiErrorMessage, useAuth } from "../../components/auth-provider";
import { ProtectedPage } from "../../components/protected-page";
import { apiRequest } from "../../lib/api-client";
import { Batch, Product, StockItem } from "../../types/api";

const ALL_ROLES = ["Super Admin", "Manager", "Pharmacist", "Staff"] as const;

export default function InventoryPage() {
  const { auth } = useAuth();
  const [productId, setProductId] = useState(1);
  const [storeId, setStoreId] = useState(1);
  const [product, setProduct] = useState<Product | null>(null);
  const [stock, setStock] = useState<StockItem[]>([]);
  const [batchNumber, setBatchNumber] = useState("");
  const [batchExpiry, setBatchExpiry] = useState("");
  const [batchQuantity, setBatchQuantity] = useState(1);
  const [createdBatches, setCreatedBatches] = useState<Batch[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const loadInventory = async () => {
    if (!auth) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [fetchedProduct, fetchedStock] = await Promise.all([
        apiRequest<Product>(`/api/inventory/products/${productId}`, { token: auth.token }) as Promise<Product>,
        apiRequest<StockItem[]>(`/api/inventory/stock/${storeId}`, { token: auth.token }) as Promise<StockItem[]>,
      ]);
      setProduct(fetchedProduct);
      setStock(fetchedStock);
    } catch (err) {
      setError(useApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const submitBatch = async (event: FormEvent) => {
    event.preventDefault();
    if (!auth) {
      return;
    }
    setError(null);
    try {
      const created = (await apiRequest<Batch>("/api/inventory/batches", {
        method: "POST",
        token: auth.token,
        body: {
          product_id: productId,
          store_id: storeId,
          batch_number: batchNumber,
          expiry_date: batchExpiry,
          quantity: batchQuantity,
        },
      })) as Batch;
      setCreatedBatches((current) => [created, ...current]);
      setBatchNumber("");
      setBatchExpiry("");
      setBatchQuantity(1);
    } catch (err) {
      setError(useApiErrorMessage(err));
    }
  };

  return (
    <ProtectedPage allowedRoles={[...ALL_ROLES]}>
      <div className="space-y-4">
        <h1 className="text-lg font-semibold text-slate-900">Inventory</h1>

        <div className="grid gap-3 rounded border border-slate-200 bg-white p-3 sm:grid-cols-3">
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
          <div className="flex items-end">
            <button
              type="button"
              onClick={() => void loadInventory()}
              className="w-full rounded bg-teal-600 px-3 py-2 text-sm text-white"
              disabled={loading}
            >
              {loading ? "Loading..." : "Load Inventory"}
            </button>
          </div>
        </div>

        {error && <p className="rounded bg-red-50 p-2 text-sm text-red-700">{error}</p>}

        {product && (
          <div className="rounded border border-slate-200 bg-white p-3 text-sm">
            <h2 className="font-medium text-slate-800">Product</h2>
            <p className="mt-1">{product.name} ({product.sku}) - {product.category}</p>
            <p>Price: {product.price} / {product.unit}</p>
          </div>
        )}

        <div className="overflow-x-auto rounded border border-slate-200 bg-white">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-100 text-left text-slate-700">
              <tr>
                <th className="px-3 py-2">Stock ID</th>
                <th className="px-3 py-2">Product ID</th>
                <th className="px-3 py-2">Store ID</th>
                <th className="px-3 py-2">Qty</th>
                <th className="px-3 py-2">Reorder</th>
                <th className="px-3 py-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {stock.map((item) => (
                <tr key={item.id} className="border-t border-slate-100">
                  <td className="px-3 py-2">{item.id}</td>
                  <td className="px-3 py-2">{item.product_id}</td>
                  <td className="px-3 py-2">{item.store_id}</td>
                  <td className="px-3 py-2">{item.quantity_on_hand}</td>
                  <td className="px-3 py-2">{item.reorder_level}</td>
                  <td className="px-3 py-2">
                    {item.quantity_on_hand <= item.reorder_level ? (
                      <span className="rounded bg-amber-100 px-2 py-0.5 text-amber-800">Reorder needed</span>
                    ) : (
                      <span className="rounded bg-emerald-100 px-2 py-0.5 text-emerald-700">OK</span>
                    )}
                  </td>
                </tr>
              ))}
              {stock.length === 0 && (
                <tr>
                  <td className="px-3 py-3 text-slate-500" colSpan={6}>
                    No stock loaded.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <form onSubmit={submitBatch} className="grid gap-3 rounded border border-slate-200 bg-white p-3 sm:grid-cols-4">
          <input
            className="border px-2 py-1 text-sm"
            placeholder="Batch number"
            value={batchNumber}
            onChange={(e) => setBatchNumber(e.target.value)}
            required
          />
          <input
            className="border px-2 py-1 text-sm"
            type="date"
            value={batchExpiry}
            onChange={(e) => setBatchExpiry(e.target.value)}
            required
          />
          <input
            className="border px-2 py-1 text-sm"
            type="number"
            min={1}
            value={batchQuantity}
            onChange={(e) => setBatchQuantity(Number(e.target.value))}
            required
          />
          <button className="rounded bg-slate-900 px-3 py-2 text-sm text-white" type="submit">
            Add Batch
          </button>
        </form>

        <div className="rounded border border-slate-200 bg-white p-3 text-sm">
          <h2 className="font-medium text-slate-800">Batch + Expiry Visibility (created in current session)</h2>
          <ul className="mt-2 space-y-1 text-slate-600">
            {createdBatches.map((batch) => (
              <li key={batch.id}>
                {batch.batch_number} - expires {batch.expiry_date} - qty {batch.quantity}
              </li>
            ))}
            {createdBatches.length === 0 && <li>No batch created in this session.</li>}
          </ul>
        </div>
      </div>
    </ProtectedPage>
  );
}

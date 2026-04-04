"use client";

import { FormEvent, useState } from "react";

import { ProtectedPage } from "../../components/protected-page";
import { useApiErrorMessage, useAuth } from "../../components/auth-provider";
import { apiRequest } from "../../lib/api-client";
import { pushActivity } from "../../lib/activity";
import { OfflineQueuedResult, Prescription, Transaction } from "../../types/api";

const BILLING_ROLES = ["Super Admin", "Pharmacist"] as const;

export default function BillingPage() {
  const { auth } = useAuth();

  const [patientId, setPatientId] = useState("");
  const [prescriptionStoreId, setPrescriptionStoreId] = useState(1);
  const [prescriptionStatus, setPrescriptionStatus] = useState("created");

  const [prescriptionId, setPrescriptionId] = useState<number>(0);
  const [transactionStoreId, setTransactionStoreId] = useState(1);
  const [productId, setProductId] = useState(1);
  const [quantity, setQuantity] = useState(1);
  const [paymentMethod, setPaymentMethod] = useState("cash");
  const [totalAmount, setTotalAmount] = useState(1);

  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const submitPrescription = async (event: FormEvent) => {
    event.preventDefault();
    if (!auth) {
      return;
    }
    setError(null);
    setMessage(null);
    try {
      const created = (await apiRequest<Prescription>("/api/billing/prescriptions", {
        method: "POST",
        token: auth.token,
        body: {
          patient_id: patientId,
          store_id: prescriptionStoreId,
          status: prescriptionStatus,
        },
        queueOnOffline: true,
      })) as Prescription | OfflineQueuedResult;

      if ("offline_queued" in created) {
        setMessage(`Prescription request queued offline at ${created.queued_at}`);
        return;
      }

      setPrescriptionId(created.id);
      pushActivity({
        id: created.id,
        type: "prescription",
        note: `Prescription #${created.id} for patient ${created.patient_id}`,
        created_at: created.created_at,
      });
      setMessage(`Prescription created successfully with ID ${created.id}`);
    } catch (err) {
      setError(useApiErrorMessage(err));
    }
  };

  const submitTransaction = async (event: FormEvent) => {
    event.preventDefault();
    if (!auth) {
      return;
    }

    setError(null);
    setMessage(null);
    try {
      const created = (await apiRequest<Transaction>("/api/billing/transactions", {
        method: "POST",
        token: auth.token,
        body: {
          prescription_id: prescriptionId,
          store_id: transactionStoreId,
          product_id: productId,
          quantity,
          payment_method: paymentMethod,
          total_amount: totalAmount,
        },
        queueOnOffline: true,
      })) as Transaction | OfflineQueuedResult;

      if ("offline_queued" in created) {
        setMessage(`Transaction request queued offline at ${created.queued_at}`);
        return;
      }

      pushActivity({
        id: created.id,
        type: "transaction",
        note: `Transaction #${created.id} for prescription ${created.prescription_id}`,
        created_at: created.created_at,
      });
      setMessage(`Transaction created successfully with ID ${created.id}`);
    } catch (err) {
      setError(useApiErrorMessage(err));
    }
  };

  return (
    <ProtectedPage allowedRoles={[...BILLING_ROLES]}>
      <div className="space-y-4">
        <h1 className="text-lg font-semibold text-slate-900">Billing</h1>

        {error && <p className="rounded bg-red-50 p-2 text-sm text-red-700">{error}</p>}
        {message && <p className="rounded bg-emerald-50 p-2 text-sm text-emerald-700">{message}</p>}

        <form onSubmit={submitPrescription} className="grid gap-3 rounded border border-slate-200 bg-white p-3 sm:grid-cols-4">
          <input
            value={patientId}
            onChange={(e) => setPatientId(e.target.value)}
            className="border px-2 py-1 text-sm"
            placeholder="Patient ID"
            required
          />
          <input
            type="number"
            min={1}
            value={prescriptionStoreId}
            onChange={(e) => setPrescriptionStoreId(Number(e.target.value))}
            className="border px-2 py-1 text-sm"
            placeholder="Store ID"
            required
          />
          <input
            value={prescriptionStatus}
            onChange={(e) => setPrescriptionStatus(e.target.value)}
            className="border px-2 py-1 text-sm"
            placeholder="Status"
            required
          />
          <button type="submit" className="rounded bg-teal-600 px-3 py-2 text-sm text-white">
            Create Prescription
          </button>
        </form>

        <form onSubmit={submitTransaction} className="grid gap-3 rounded border border-slate-200 bg-white p-3 sm:grid-cols-3">
          <input
            type="number"
            min={1}
            value={prescriptionId || ""}
            onChange={(e) => setPrescriptionId(Number(e.target.value))}
            className="border px-2 py-1 text-sm"
            placeholder="Prescription ID"
            required
          />
          <input
            type="number"
            min={1}
            value={transactionStoreId}
            onChange={(e) => setTransactionStoreId(Number(e.target.value))}
            className="border px-2 py-1 text-sm"
            placeholder="Store ID"
            required
          />
          <input
            type="number"
            min={1}
            value={productId}
            onChange={(e) => setProductId(Number(e.target.value))}
            className="border px-2 py-1 text-sm"
            placeholder="Product ID"
            required
          />
          <input
            type="number"
            min={1}
            value={quantity}
            onChange={(e) => setQuantity(Number(e.target.value))}
            className="border px-2 py-1 text-sm"
            placeholder="Quantity"
            required
          />
          <input
            value={paymentMethod}
            onChange={(e) => setPaymentMethod(e.target.value)}
            className="border px-2 py-1 text-sm"
            placeholder="Payment method"
            required
          />
          <input
            type="number"
            step="0.01"
            min={0.01}
            value={totalAmount}
            onChange={(e) => setTotalAmount(Number(e.target.value))}
            className="border px-2 py-1 text-sm"
            placeholder="Total amount"
            required
          />
          <button type="submit" className="rounded bg-slate-900 px-3 py-2 text-sm text-white sm:col-span-3">
            Create Transaction
          </button>
        </form>
      </div>
    </ProtectedPage>
  );
}

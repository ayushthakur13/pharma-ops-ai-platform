"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { useApiErrorMessage } from "../../components/auth-provider";
import { apiRequest } from "../../lib/api-client";
import { RegisterResponse, UserRole } from "../../types/api";

const ROLE_OPTIONS: UserRole[] = ["Staff", "Pharmacist", "Manager", "Super Admin"];

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [role, setRole] = useState<UserRole>("Staff");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    setSuccess(null);

    try {
      const created = (await apiRequest<RegisterResponse>("/api/auth/register", {
        method: "POST",
        body: {
          email,
          password,
          first_name: firstName,
          last_name: lastName,
          role,
        },
      })) as RegisterResponse;

      setSuccess(`Account created for ${created.email}. You can login now.`);
      setTimeout(() => router.push("/login"), 800);
    } catch (err) {
      setError(useApiErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto mt-10 w-full max-w-lg rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <h1 className="text-xl font-semibold text-slate-900">Register</h1>
      <p className="mt-1 text-sm text-slate-600">Create a role-based account for platform access.</p>

      <form className="mt-4 grid gap-3" onSubmit={onSubmit}>
        <input
          className="w-full border px-3 py-2 text-sm"
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <input
          className="w-full border px-3 py-2 text-sm"
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          minLength={8}
          required
        />
        <div className="grid gap-3 sm:grid-cols-2">
          <input
            className="w-full border px-3 py-2 text-sm"
            type="text"
            placeholder="First name"
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
            required
          />
          <input
            className="w-full border px-3 py-2 text-sm"
            type="text"
            placeholder="Last name"
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            required
          />
        </div>
        <select
          className="w-full border px-3 py-2 text-sm"
          value={role}
          onChange={(e) => setRole(e.target.value as UserRole)}
        >
          {ROLE_OPTIONS.map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </select>

        {error && <p className="text-sm text-red-600">{error}</p>}
        {success && <p className="text-sm text-emerald-700">{success}</p>}

        <button
          type="submit"
          className="rounded bg-teal-600 px-3 py-2 text-sm font-medium text-white disabled:opacity-60"
          disabled={submitting}
        >
          {submitting ? "Creating account..." : "Create Account"}
        </button>
      </form>

      <p className="mt-3 text-sm text-slate-600">
        Already registered? <Link href="/login" className="text-teal-700 underline">Go to login</Link>
      </p>
    </div>
  );
}

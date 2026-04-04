import type { Metadata } from "next";

import { AppShell } from "../components/app-shell";
import { AuthProvider } from "../components/auth-provider";

import "./globals.css";

export const metadata: Metadata = {
  title: "Pharma Ops Frontend",
  description: "Mobile-first interface for Pharma Ops AI Platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <AppShell>{children}</AppShell>
        </AuthProvider>
      </body>
    </html>
  );
}

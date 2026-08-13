import type { Metadata } from "next";
import AppShell from "@/components/AppShell";
import Onboarding from "@/components/Onboarding";

export const metadata: Metadata = {
  title: "Áttekintés",
};

/** Authenticated shell — wraps every app page with nav + onboarding. */
export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <AppShell>
      {children}
      <Onboarding />
    </AppShell>
  );
}

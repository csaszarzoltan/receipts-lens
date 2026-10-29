import type { Metadata } from "next";
import AppShell from "@/components/AppShell";
import Onboarding from "@/components/Onboarding";

export const metadata: Metadata = {
  title: "Overview",
};

/** Authenticated shell — wraps every app page with nav; first-run onboarding sits above the page. */
export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <AppShell>
      <Onboarding />
      {children}
    </AppShell>
  );
}

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { cn } from "@/lib/utils";

const TABS = [
  { href: "/staff/dashboard", label: "Dashboard", icon: "🏠" },
  { href: "/staff/deliveries", label: "Deliveries", icon: "🚴" },
  { href: "/staff/attendance", label: "Attendance", icon: "🗓" },
  { href: "/staff/salary", label: "Salary", icon: "💰" },
  { href: "/staff/profile", label: "Profile", icon: "👤" },
];

export default function StaffLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { requireAuth, isHydrating } = useAuth();
  requireAuth(["staff"]);
  const pathname = usePathname();

  if (isHydrating) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-crust-50">
      <main className="flex-1 pb-20">{children}</main>

      <nav className="fixed bottom-0 left-0 right-0 z-40 grid grid-cols-5 border-t border-crust-200 bg-white">
        {TABS.map((tab) => {
          const active = pathname.startsWith(tab.href);
          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={cn(
                "flex flex-col items-center gap-1 py-3 text-xs",
                active ? "text-crust-700" : "text-crust-400",
              )}
            >
              <span className="text-xl" aria-hidden>
                {tab.icon}
              </span>
              {tab.label}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}

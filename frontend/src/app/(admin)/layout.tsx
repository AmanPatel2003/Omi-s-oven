"use client";

import { useAuth } from "@/hooks/useAuth";
import { AdminSidebar } from "@/components/layout/AdminSidebar";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { requireAuth, isHydrating } = useAuth();
  requireAuth(["admin", "super_admin"]);

  if (isHydrating) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen">
      <AdminSidebar />
      <main className="flex-1 bg-crust-50 p-6">{children}</main>
    </div>
  );
}

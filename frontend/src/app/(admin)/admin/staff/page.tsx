"use client";

import { useState } from "react";
import { useAppSelector } from "@/store/hooks";
import { useGetStaffListQuery } from "@/store/api/adminStaffApi";
import { StaffCreateModal } from "@/components/admin/StaffCreateModal";
import { DataTable } from "@/components/admin/DataTable";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";

export default function AdminStaffPage() {
  const currentUserRole = useAppSelector((state) => state.auth.user?.role);
  const isSuperAdmin = currentUserRole === "super_admin";

  const [roleFilter, setRoleFilter] = useState("");
  const { data: staff, isLoading } = useGetStaffListQuery(
    roleFilter ? { role: roleFilter } : undefined,
  );
  const [showCreateModal, setShowCreateModal] = useState(false);

  return (
    <div className="mx-auto max-w-4xl">
      <div className="flex items-center justify-between">
        <h1 className="font-display text-2xl font-semibold text-crust-900">
          Staff
        </h1>
        {isSuperAdmin && (
          <Button
            className="w-auto px-4"
            onClick={() => setShowCreateModal(true)}
          >
            Add Staff
          </Button>
        )}
      </div>

      <div className="mt-4">
        <select
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
          className="rounded-xl border border-crust-200 px-3 py-2 text-sm"
        >
          <option value="">All roles</option>
          <option value="delivery_staff">Delivery Staff</option>
          <option value="baker">Baker</option>
          <option value="admin">Admin</option>
        </select>
      </div>

      <div className="mt-4">
        <DataTable
          rows={staff ?? []}
          emptyMessage={isLoading ? "Loading…" : "No staff found."}
          rowHref={(s) => `/admin/staff/${s.id}`}
          columns={[
            { header: "Name", render: (s) => s.name },
            { header: "Role", render: (s) => s.role },
            { header: "Email", render: (s) => s.email },
            {
              header: "Status",
              render: (s) => (
                <span
                  className={cn(
                    "rounded-full px-2 py-0.5 text-xs font-medium",
                    s.isActive
                      ? "bg-green-100 text-green-700"
                      : "bg-crust-100 text-crust-500",
                  )}
                >
                  {s.isActive ? "Active" : "Inactive"}
                </span>
              ),
            },
          ]}
        />
      </div>

      {showCreateModal && (
        <StaffCreateModal onClose={() => setShowCreateModal(false)} />
      )}
    </div>
  );
}

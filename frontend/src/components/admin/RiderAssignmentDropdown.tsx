"use client";

import { useGetStaffByRoleQuery } from "@/store/api/adminStaffApi";
import { useAssignRiderMutation } from "@/store/api/adminOrdersApi";
import type { AdminOrder } from "@/types/api";

export function RiderAssignmentDropdown({ order }: { order: AdminOrder }) {
  const { data: riders } = useGetStaffByRoleQuery("delivery_staff");
  const [assignRider, { isLoading }] = useAssignRiderMutation();

  const enabled = order.status === "confirmed" || order.status === "preparing";

  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-sm font-medium text-crust-800">
        Delivery rider
      </label>
      <select
        value={order.riderId ?? ""}
        disabled={!enabled || isLoading}
        onChange={(e) =>
          e.target.value &&
          assignRider({ id: order.id, riderId: e.target.value })
        }
        className="rounded-xl border border-crust-200 px-3 py-2 text-sm disabled:bg-crust-50 disabled:text-crust-400"
      >
        <option value="">{order.riderName ?? "Unassigned"}</option>
        {riders?.map((r) => (
          <option key={r.id} value={r.id}>
            {r.name}
          </option>
        ))}
      </select>
      {!enabled && (
        <p className="text-xs text-crust-400">
          Only assignable once the order is confirmed or preparing.
        </p>
      )}
    </div>
  );
}

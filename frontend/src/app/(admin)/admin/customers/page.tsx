"use client";

import { useState } from "react";
import {
  useGetAdminCustomersQuery,
  useToggleCustomerBlockMutation,
} from "@/store/api/adminCustomersApi";
import { DataTable } from "@/components/admin/DataTable";
import { ConfirmDialog } from "@/components/admin/ConfirmDialog";
import { Button } from "@/components/ui/Button";
import { useDebounce } from "@/hooks/useDebounce";
import { cn, formatCurrency } from "@/lib/utils";
import type { AdminCustomer } from "@/types/api";

export default function AdminCustomersPage() {
  const [page, setPage] = useState(1);
  const [searchInput, setSearchInput] = useState("");
  const search = useDebounce(searchInput, 400);
  const { data, isLoading } = useGetAdminCustomersQuery({
    page,
    search: search || undefined,
  });
  const [toggleBlock, { isLoading: isToggling }] =
    useToggleCustomerBlockMutation();
  const [blockTarget, setBlockTarget] = useState<AdminCustomer | null>(null);

  const totalPages = data
    ? Math.max(1, Math.ceil(data.total / data.pageSize))
    : 1;

  async function handleConfirmToggle() {
    if (!blockTarget) return;
    await toggleBlock({
      id: blockTarget.id,
      isBlocked: !blockTarget.isBlocked,
    });
    setBlockTarget(null);
  }

  return (
    <div className="mx-auto max-w-5xl">
      <h1 className="font-display text-2xl font-semibold text-crust-900">
        Customers
      </h1>

      <div className="mt-4">
        <input
          type="search"
          placeholder="Search by name, email, or phone…"
          value={searchInput}
          onChange={(e) => {
            setSearchInput(e.target.value);
            setPage(1);
          }}
          className="rounded-xl border border-crust-200 px-3 py-2 text-sm"
        />
      </div>

      <div className="mt-4">
        <DataTable
          rows={data?.items ?? []}
          emptyMessage={isLoading ? "Loading…" : "No customers found."}
          rowHref={(c) => `/admin/customers/${c.id}`}
          columns={[
            { header: "Name", render: (c) => c.name },
            { header: "Orders", render: (c) => c.orderCount, align: "right" },
            {
              header: "Total spend",
              render: (c) => formatCurrency(c.totalSpend),
              align: "right",
            },
            { header: "Points", render: (c) => c.rewardPoints, align: "right" },
            {
              header: "Status",
              render: (c) => (
                <span
                  className={cn(
                    "rounded-full px-2 py-0.5 text-xs font-medium",
                    c.isBlocked
                      ? "bg-red-100 text-red-700"
                      : "bg-green-100 text-green-700",
                  )}
                >
                  {c.isBlocked ? "Blocked" : "Active"}
                </span>
              ),
            },
            {
              header: "",
              render: (c) => (
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setBlockTarget(c);
                  }}
                  className="text-xs text-crust-600 underline"
                >
                  {c.isBlocked ? "Unblock" : "Block"}
                </button>
              ),
              align: "right",
            },
          ]}
        />
      </div>

      {data && totalPages > 1 && (
        <div className="mt-4 flex items-center justify-center gap-3">
          <Button
            variant="secondary"
            className="w-auto px-3"
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
          >
            Previous
          </Button>
          <span className="text-sm text-crust-600">
            Page {page} of {totalPages}
          </span>
          <Button
            variant="secondary"
            className="w-auto px-3"
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </Button>
        </div>
      )}

      {blockTarget && (
        <ConfirmDialog
          title={`${blockTarget.isBlocked ? "Unblock" : "Block"} ${blockTarget.name}?`}
          description={
            blockTarget.isBlocked
              ? "They'll be able to sign in and place orders again immediately."
              : "They won't be able to place new orders or sign in while blocked. Existing orders are unaffected."
          }
          isDangerous={!blockTarget.isBlocked}
          isLoading={isToggling}
          confirmLabel={blockTarget.isBlocked ? "Unblock" : "Block"}
          onConfirm={handleConfirmToggle}
          onCancel={() => setBlockTarget(null)}
        />
      )}
    </div>
  );
}

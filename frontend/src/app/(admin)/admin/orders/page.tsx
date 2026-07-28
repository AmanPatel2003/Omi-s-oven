"use client";

import { useState } from "react";
import { useGetAdminOrdersQuery } from "@/store/api/adminOrdersApi";
import { useExportOrdersCsv } from "@/hooks/useExportOrdersCsv";
import { DataTable } from "@/components/admin/DataTable";
import {
  OrderStatusBadge,
  ORDER_STATUS_STYLES,
  ORDER_STATUS_LABELS,
} from "@/components/orders/OrderStatusBadge";
import { Button } from "@/components/ui/Button";
import { useDebounce } from "@/hooks/useDebounce";
import { ORDER_STATUSES, type OrderStatus } from "@/lib/constants";
import { cn, formatCurrency, formatDate } from "@/lib/utils";

export default function AdminOrdersPage() {
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState<OrderStatus | "">("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const search = useDebounce(searchInput, 400);

  const { data, isLoading } = useGetAdminOrdersQuery({
    page,
    status: status || undefined,
    from: from || undefined,
    to: to || undefined,
    search: search || undefined,
  });
  const { exportOrdersCsv, isExporting } = useExportOrdersCsv();

  const totalPages = data
    ? Math.max(1, Math.ceil(data.total / data.pageSize))
    : 1;

  return (
    <div className="mx-auto max-w-6xl">
      <div className="flex items-center justify-between">
        <h1 className="font-display text-2xl font-semibold text-crust-900">
          Orders
        </h1>
        <Button
          variant="secondary"
          className="w-auto px-4"
          isLoading={isExporting}
          onClick={() =>
            exportOrdersCsv({ from: from || undefined, to: to || undefined })
          }
        >
          Export CSV
        </Button>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => {
            setStatus("");
            setPage(1);
          }}
          className={cn(
            "rounded-full px-2.5 py-0.5 text-xs font-medium",
            status === ""
              ? "bg-crust-600 text-white"
              : "bg-crust-100 text-crust-600",
          )}
        >
          All
        </button>
        {ORDER_STATUSES.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => {
              setStatus(s);
              setPage(1);
            }}
            className={cn(
              "rounded-full px-2.5 py-0.5 text-xs font-medium",
              status === s ? "ring-2 ring-crust-600" : "",
              ORDER_STATUS_STYLES[s],
            )}
          >
            {ORDER_STATUS_LABELS[s]}
          </button>
        ))}
      </div>

      <div className="mt-4 flex flex-wrap gap-3">
        <input
          type="search"
          placeholder="Search by customer or order id…"
          value={searchInput}
          onChange={(e) => {
            setSearchInput(e.target.value);
            setPage(1);
          }}
          className="rounded-xl border border-crust-200 px-3 py-2 text-sm"
        />
        <input
          type="date"
          value={from}
          onChange={(e) => {
            setFrom(e.target.value);
            setPage(1);
          }}
          className="rounded-xl border border-crust-200 px-3 py-2 text-sm"
        />
        <input
          type="date"
          value={to}
          onChange={(e) => {
            setTo(e.target.value);
            setPage(1);
          }}
          className="rounded-xl border border-crust-200 px-3 py-2 text-sm"
        />
      </div>

      <div className="mt-4">
        <DataTable
          rows={data?.items ?? []}
          emptyMessage={isLoading ? "Loading…" : "No orders found."}
          rowHref={(o) => `/admin/orders/${o.id}`}
          columns={[
            { header: "Order", render: (o) => `#${o.id.slice(-8)}` },
            { header: "Customer", render: (o) => o.customerName },
            {
              header: "Status",
              render: (o) => <OrderStatusBadge status={o.status} />,
            },
            { header: "Placed", render: (o) => formatDate(o.createdAt) },
            {
              header: "Total",
              render: (o) => formatCurrency(o.total),
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
    </div>
  );
}

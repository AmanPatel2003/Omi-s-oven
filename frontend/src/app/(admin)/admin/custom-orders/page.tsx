"use client";

import { useState } from "react";
import Link from "next/link";
import { useGetAdminCustomOrdersQuery } from "@/store/api/adminCustomOrdersApi";
import { CustomOrderStatusBadge } from "@/components/custom-orders/CustomOrderStatusBadge";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { cn, formatCurrency, formatDate } from "@/lib/utils";
import { CUSTOM_ORDER_STATUSES, type CustomOrderStatus } from "@/lib/constants";

const NEEDS_QUOTE: CustomOrderStatus[] = ["pending", "reviewing"];

export default function AdminCustomOrdersPage() {
  const [filter, setFilter] = useState<CustomOrderStatus[] | null>(null);
  const { data: orders, isLoading } = useGetAdminCustomOrdersQuery(
    filter ?? undefined,
  );

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="font-display text-2xl font-semibold text-crust-900">
        Custom Cake Requests
      </h1>

      <div className="mt-4 flex flex-wrap gap-2">
        <FilterChip
          label="Needs Quote"
          active={!!filter && filter.join() === NEEDS_QUOTE.join()}
          onClick={() => setFilter(NEEDS_QUOTE)}
          highlight
        />
        <FilterChip
          label="All"
          active={filter === null}
          onClick={() => setFilter(null)}
        />
        {CUSTOM_ORDER_STATUSES.map((s) => (
          <FilterChip
            key={s}
            label={s.replace(/_/g, " ")}
            active={!!filter && filter.length === 1 && filter[0] === s}
            onClick={() => setFilter([s])}
          />
        ))}
      </div>

      <div className="mt-6">
        {isLoading ? (
          <div className="flex justify-center py-8">
            <LoadingSpinner />
          </div>
        ) : !orders || orders.length === 0 ? (
          <p className="py-8 text-center text-sm text-crust-500">
            No requests match this filter.
          </p>
        ) : (
          <div className="flex flex-col gap-3">
            {orders.map((order) => (
              <Link
                key={order.id}
                href={`/admin/custom-orders/${order.id}`}
                className="flex items-center justify-between rounded-xl border border-crust-100 bg-white p-4"
              >
                <div>
                  <p className="text-sm font-medium text-crust-900">
                    {order.occasion}
                  </p>
                  <p className="text-xs text-crust-500">
                    {order.customerName} · {formatDate(order.createdAt)}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  {order.quotedPrice != null && (
                    <span className="text-sm font-semibold text-teal-700">
                      {formatCurrency(order.quotedPrice)}
                    </span>
                  )}
                  <CustomOrderStatusBadge status={order.status} />
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function FilterChip({
  label,
  active,
  onClick,
  highlight,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
  highlight?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "rounded-full px-3 py-1 text-xs font-medium capitalize",
        active
          ? "bg-crust-600 text-white"
          : highlight
            ? "bg-teal-100 text-teal-700"
            : "bg-crust-100 text-crust-600",
      )}
    >
      {label}
    </button>
  );
}

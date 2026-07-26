"use client";

import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";
import { useGetCustomOrdersQuery } from "@/store/api/customOrdersApi";
import { CustomOrderStatusBadge } from "@/components/custom-orders/CustomOrderStatusBadge";
import { Button } from "@/components/ui/Button";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { formatCurrency, formatDate } from "@/lib/utils";

export default function CustomOrdersPage() {
  const { requireAuth, isHydrating } = useAuth();
  requireAuth();

  const { data: orders, isLoading } = useGetCustomOrdersQuery();

  if (isHydrating || isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <div className="flex items-center justify-between">
        <h1 className="font-display text-2xl font-semibold text-crust-900">
          Custom Cake Requests
        </h1>
        <Link href="/custom-orders/new">
          <Button className="w-auto px-4">New request</Button>
        </Link>
      </div>

      {!orders || orders.length === 0 ? (
        <p className="mt-8 text-center text-sm text-crust-500">
          No custom cake requests yet.
        </p>
      ) : (
        <div className="mt-6 flex flex-col gap-3">
          {orders.map((order) => (
            <Link
              key={order.id}
              href={`/custom-orders/${order.id}`}
              className="flex items-center justify-between rounded-xl border border-crust-100 bg-white p-4"
            >
              <div>
                <p className="text-sm font-medium text-crust-900">
                  {order.occasion}
                </p>
                <p className="text-xs text-crust-500">
                  {formatDate(order.createdAt)}
                </p>
              </div>
              <div className="flex items-center gap-3">
                {order.status === "quoted" && order.quotedPrice != null && (
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
  );
}

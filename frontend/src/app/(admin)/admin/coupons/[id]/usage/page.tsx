"use client";

import { useState } from "react";
import { useGetCouponUsageQuery } from "@/store/api/adminCouponsApi";
import { Button } from "@/components/ui/Button";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { formatCurrency, formatDate } from "@/lib/utils";

export default function CouponUsagePage({
  params,
}: {
  params: { id: string };
}) {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useGetCouponUsageQuery({ id: params.id, page });

  if (isLoading || !data) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  const totalPages = Math.max(1, Math.ceil(data.total / data.pageSize));

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="font-display text-2xl font-semibold text-crust-900">
        Coupon Usage
      </h1>

      {data.items.length === 0 ? (
        <p className="mt-8 text-center text-sm text-crust-500">
          This coupon hasn't been used yet.
        </p>
      ) : (
        <div className="mt-6 overflow-hidden rounded-xl border border-crust-100 bg-white">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-crust-100 bg-crust-50 text-left text-xs font-medium text-crust-500">
                <th className="px-3 py-2">Customer</th>
                <th className="px-3 py-2">Order</th>
                <th className="px-3 py-2 text-right">Discount</th>
                <th className="px-3 py-2 text-right">Used</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((entry) => (
                <tr
                  key={entry.id}
                  className="border-b border-crust-50 last:border-0"
                >
                  <td className="px-3 py-2">{entry.customerName}</td>
                  <td className="px-3 py-2">#{entry.orderId.slice(-8)}</td>
                  <td className="px-3 py-2 text-right">
                    {formatCurrency(entry.discountApplied)}
                  </td>
                  <td className="px-3 py-2 text-right text-crust-500">
                    {formatDate(entry.usedAt)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {totalPages > 1 && (
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

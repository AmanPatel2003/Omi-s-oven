"use client";

import { useAuth } from "@/hooks/useAuth";
import { usePagination } from "@/hooks/usePagination";
import { useGetOrdersQuery } from "@/store/api/ordersApi";
import { OrderCard } from "@/components/orders/OrderCard";
import { Button } from "@/components/ui/Button";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";

export default function OrdersPage() {
  const { requireAuth, isHydrating } = useAuth();
  requireAuth();

  const { page, setPage } = usePagination();
  const { data, isLoading } = useGetOrdersQuery({ page });

  if (isHydrating || isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  if (!data || data.items.length === 0) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16 text-center">
        <p className="text-crust-600">No orders yet.</p>
      </div>
    );
  }

  const totalPages = Math.max(1, Math.ceil(data.total / data.pageSize));

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="font-display text-2xl font-semibold text-crust-900">
        Your Orders
      </h1>

      <div className="mt-6 flex flex-col gap-4">
        {data.items.map((order) => (
          <OrderCard key={order.id} order={order} />
        ))}
      </div>

      {totalPages > 1 && (
        <div className="mt-6 flex items-center justify-center gap-3">
          <Button
            variant="secondary"
            className="w-auto px-3"
            disabled={page <= 1}
            onClick={() => setPage(page - 1)}
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
            onClick={() => setPage(page + 1)}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
}

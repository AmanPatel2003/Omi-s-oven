"use client";

import { useAuth } from "@/hooks/useAuth";
import {
  useGetCustomOrderByIdQuery,
  useAcceptQuoteMutation,
} from "@/store/api/customOrdersApi";
import { CustomOrderStatusBadge } from "@/components/custom-orders/CustomOrderStatusBadge";
import { Button } from "@/components/ui/Button";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { formatCurrency, formatDate } from "@/lib/utils";

export default function CustomOrderDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const { requireAuth, isHydrating } = useAuth();
  requireAuth();

  const { data: order, isLoading } = useGetCustomOrderByIdQuery(params.id);
  const [acceptQuote, { isLoading: isAccepting }] = useAcceptQuoteMutation();

  if (isHydrating || isLoading || !order) {
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
          {order.occasion}
        </h1>
        <CustomOrderStatusBadge status={order.status} />
      </div>
      <p className="mt-1 text-sm text-crust-500">
        Requested {formatDate(order.createdAt)}
      </p>

      {order.status === "quoted" && order.quotedPrice != null && (
        <div className="mt-6 rounded-xl border-2 border-teal-600 bg-teal-50 p-5">
          <p className="text-sm font-medium text-teal-800">
            Your quote is ready
          </p>
          <p className="mt-1 text-3xl font-semibold text-teal-900">
            {formatCurrency(order.quotedPrice)}
          </p>
          <Button
            className="mt-4 w-fit bg-teal-700 hover:bg-teal-800"
            isLoading={isAccepting}
            onClick={() => acceptQuote(order.id)}
          >
            Accept Quote
          </Button>
        </div>
      )}

      <div className="mt-6 flex flex-col gap-4 rounded-xl border border-crust-100 bg-white p-4 text-sm">
        <Detail label="Flavor" value={order.flavor} />
        <Detail label="Size" value={order.size} />
        <Detail label="Shape" value={order.shape} />
        {order.message && (
          <Detail label="Message on cake" value={order.message} />
        )}
        <Detail
          label="Budget"
          value={`${formatCurrency(order.budgetMin)} – ${formatCurrency(order.budgetMax)}`}
        />
        <Detail
          label="Needed by"
          value={formatDate(order.neededBy, "d MMM yyyy, h:mm a")}
        />
        <Detail
          label="Delivery"
          value={order.addressId ? "Delivery" : "Store pickup"}
        />
      </div>
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4">
      <span className="text-crust-500">{label}</span>
      <span className="text-right text-crust-800">{value}</span>
    </div>
  );
}

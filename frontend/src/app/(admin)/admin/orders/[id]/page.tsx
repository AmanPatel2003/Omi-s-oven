"use client";

import { useGetAdminOrderByIdQuery } from "@/store/api/adminOrdersApi";
import { OrderStatusBadge } from "@/components/orders/OrderStatusBadge";
import { OrderTimeline } from "@/components/orders/OrderTimeline";
import { StatusTransitionButton } from "@/components/admin/StatusTransitionButton";
import { RiderAssignmentDropdown } from "@/components/admin/RiderAssignmentDropdown";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { formatCurrency, formatDate } from "@/lib/utils";

export default function AdminOrderDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const { data: order, isLoading } = useGetAdminOrderByIdQuery(params.id);

  if (isLoading || !order) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-semibold text-crust-900">
            Order #{order.id.slice(-8)}
          </h1>
          <p className="mt-1 text-sm text-crust-500">
            {order.customerName} · {order.customerEmail}
          </p>
        </div>
        <OrderStatusBadge status={order.status} />
      </div>

      <div className="mt-4">
        <StatusTransitionButton
          orderId={order.id}
          currentStatus={order.status}
        />
      </div>

      <div className="mt-6 grid gap-8 md:grid-cols-[1fr_320px]">
        <div className="flex flex-col gap-6">
          <section>
            <h2 className="text-sm font-semibold text-crust-800">Status</h2>
            <div className="mt-3">
              <OrderTimeline history={order.statusHistory} />
            </div>
          </section>

          <section>
            <h2 className="text-sm font-semibold text-crust-800">Items</h2>
            <ul className="mt-3 flex flex-col gap-2">
              {order.items.map((item, i) => (
                <li
                  key={i}
                  className="flex justify-between text-sm text-crust-700"
                >
                  <span>
                    {item.name}
                    {item.variantLabel ? ` (${item.variantLabel})` : ""} ×{" "}
                    {item.quantity}
                  </span>
                  <span>{formatCurrency(item.unitPrice * item.quantity)}</span>
                </li>
              ))}
            </ul>
          </section>

          <section>
            <h2 className="text-sm font-semibold text-crust-800">
              Delivery address
            </h2>
            <p className="mt-2 text-sm text-crust-700">
              {order.address.addressLine1}
              {order.address.addressLine2
                ? `, ${order.address.addressLine2}`
                : ""}
              <br />
              {order.address.city}, {order.address.state}{" "}
              {order.address.postalCode}
              <br />
              {order.address.phone}
            </p>
          </section>
        </div>

        <div className="flex flex-col gap-4">
          <div className="rounded-xl border border-crust-100 bg-white p-4">
            <RiderAssignmentDropdown order={order} />
          </div>

          <div className="flex flex-col gap-2 rounded-xl border border-crust-100 bg-white p-4 text-sm">
            <Row label="Subtotal" value={order.subtotal} />
            {order.discount > 0 && (
              <Row label="Discount" value={-order.discount} />
            )}
            {order.pointsDiscount > 0 && (
              <Row label="Points redeemed" value={-order.pointsDiscount} />
            )}
            <Row label="Tax" value={order.tax} />
            <Row label="Delivery" value={order.deliveryFee} />
            <div className="mt-1 flex justify-between border-t border-crust-100 pt-2 font-semibold text-crust-900">
              <span>Total</span>
              <span>{formatCurrency(order.total)}</span>
            </div>
            <p className="mt-2 text-xs text-crust-500">
              {order.paymentMethod === "cod"
                ? "Cash on delivery"
                : `Online — ${order.paymentStatus}`}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex justify-between text-crust-700">
      <span>{label}</span>
      <span>{formatCurrency(value)}</span>
    </div>
  );
}

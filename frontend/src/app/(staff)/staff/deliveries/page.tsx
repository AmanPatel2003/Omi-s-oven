"use client";

import { useState } from "react";
import {
  useGetAssignedOrdersQuery,
  useMarkPickedUpMutation,
} from "@/store/api/staffApi";
import { useDeliveryLocationTracking } from "@/hooks/useDeliveryLocationTracking";
import { DeliveredOtpModal } from "@/components/staff/DeliveredOtpModal";
import { OrderStatusBadge } from "@/components/orders/OrderStatusBadge";
import { Button } from "@/components/ui/Button";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";

export default function StaffDeliveriesPage() {
  const { data: orders, isLoading } = useGetAssignedOrdersQuery();
  const [markPickedUp, { isLoading: isMarkingPickedUp }] =
    useMarkPickedUpMutation();
  const [otpTarget, setOtpTarget] = useState<string | null>(null);

  const hasActiveDelivery = (orders ?? []).some(
    (o) => o.status === "out_for_delivery",
  );
  useDeliveryLocationTracking(hasActiveDelivery);

  if (isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-md px-4 py-6">
      <h1 className="font-display text-2xl font-semibold text-crust-900">
        Deliveries
      </h1>

      {hasActiveDelivery && (
        <p className="mt-3 rounded-xl bg-crust-100 px-3 py-2 text-xs text-crust-600">
          We're sharing your location with the customer while a delivery is in
          progress, so they can track their order. This stops automatically once
          it's delivered.
        </p>
      )}

      {!orders || orders.length === 0 ? (
        <p className="mt-8 text-center text-sm text-crust-500">
          No deliveries assigned right now.
        </p>
      ) : (
        <div className="mt-4 flex flex-col gap-3">
          {orders.map((order) => (
            <div
              key={order.id}
              className="rounded-2xl border border-crust-100 bg-white p-4"
            >
              <div className="flex items-center justify-between">
                <p className="font-medium text-crust-900">
                  {order.customerName}
                </p>
                <OrderStatusBadge status={order.status} />
              </div>
              <p className="mt-1 text-sm text-crust-600">
                {order.address.addressLine1}
                {order.address.addressLine2
                  ? `, ${order.address.addressLine2}`
                  : ""}
                , {order.address.city}
              </p>
              <a
                href={`tel:${order.customerPhone}`}
                className="mt-1 block text-sm text-crust-700 underline"
              >
                {order.customerPhone}
              </a>

              <div className="mt-3">
                {(order.status === "confirmed" ||
                  order.status === "preparing") && (
                  <Button
                    isLoading={isMarkingPickedUp}
                    onClick={() => markPickedUp(order.id)}
                  >
                    Mark Picked Up
                  </Button>
                )}
                {order.status === "out_for_delivery" && (
                  <Button onClick={() => setOtpTarget(order.id)}>
                    Mark Delivered
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {otpTarget && (
        <DeliveredOtpModal
          orderId={otpTarget}
          onClose={() => setOtpTarget(null)}
        />
      )}
    </div>
  );
}

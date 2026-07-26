"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { useAuth } from "@/hooks/useAuth";
import { useGetOrderByIdQuery } from "@/store/api/ordersApi";
import { useTrackDeliveryQuery } from "@/store/api/deliveryApi";
import { OrderStatusBadge } from "@/components/orders/OrderStatusBadge";
import { OrderTimeline } from "@/components/orders/OrderTimeline";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { formatCurrency, formatDate } from "@/lib/utils";

const DeliveryMap = dynamic(
  () => import("@/components/orders/DeliveryMap").then((m) => m.DeliveryMap),
  {
    ssr: false,
    loading: () => <div className="h-64 rounded-xl bg-crust-50" />,
  },
);

export default function OrderDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const { requireAuth, isHydrating } = useAuth();
  requireAuth();

  const [shouldPoll, setShouldPoll] = useState(true);
  const { data: order, isLoading } = useGetOrderByIdQuery(params.id, {
    pollingInterval: shouldPoll ? 3000 : undefined,
  });

  useEffect(() => {
    if (!order) return;
    const stillConfirming =
      order.paymentMethod === "online" && order.paymentStatus === "pending";
    setShouldPoll(stillConfirming);
  }, [order]);

  if (isHydrating || isLoading || !order) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <div className="flex items-center justify-between">
        <h1 className="font-display text-2xl font-semibold text-crust-900">
          Order #{order.id.slice(-8)}
        </h1>
        <OrderStatusBadge status={order.status} />
      </div>
      <p className="mt-1 text-sm text-crust-500">
        Placed {formatDate(order.createdAt)}
      </p>

      <div className="mt-6 grid gap-8 md:grid-cols-[1fr_320px]">
        <div className="flex flex-col gap-6">
          <section>
            <h2 className="text-sm font-semibold text-crust-800">Status</h2>
            <div className="mt-3">
              <OrderTimeline history={order.statusHistory} />
            </div>
          </section>

          {order.status === "out_for_delivery" && (
            <LiveTracking orderId={order.id} />
          )}

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

        <div className="flex flex-col gap-2 rounded-xl border border-crust-100 bg-white p-4 text-sm">
          <Row label="Subtotal" value={order.subtotal} />
          {order.discount > 0 && (
            <Row label="Coupon discount" value={-order.discount} />
          )}
          {order.pointsDiscount > 0 && (
            <Row label="Rewards redeemed" value={-order.pointsDiscount} />
          )}
          <Row label="Tax" value={order.tax} />
          <Row
            label="Delivery"
            value={order.deliveryFee}
            override={order.deliveryFee === 0 ? "Free" : undefined}
          />
          <div className="mt-1 flex justify-between border-t border-crust-100 pt-2 font-semibold text-crust-900">
            <span>Total</span>
            <span>{formatCurrency(order.total)}</span>
          </div>
          <p className="mt-2 text-xs text-crust-500">
            {order.paymentMethod === "cod"
              ? "Cash on delivery"
              : order.paymentStatus === "pending"
                ? "Payment received, confirming…"
                : order.paymentStatus === "paid"
                  ? "Paid online"
                  : "Payment failed"}
          </p>
        </div>
      </div>
    </div>
  );
}

function Row({
  label,
  value,
  override,
}: {
  label: string;
  value: number;
  override?: string;
}) {
  return (
    <div className="flex justify-between text-crust-700">
      <span>{label}</span>
      <span>{override ?? formatCurrency(value)}</span>
    </div>
  );
}

function LiveTracking({ orderId }: { orderId: string }) {
  const [delivered, setDelivered] = useState(false);
  const { data: tracking } = useTrackDeliveryQuery(orderId, {
    pollingInterval: 15_000,
    skip: delivered,
  });

  useEffect(() => {
    if (tracking?.deliveredAt) setDelivered(true);
  }, [tracking]);

  return (
    <section className="rounded-xl border border-crust-100 bg-white p-4">
      <h2 className="text-sm font-semibold text-crust-800">Live tracking</h2>
      <div className="mt-3">
        <DeliveryMap
          latitude={tracking?.currentLocation?.latitude ?? null}
          longitude={tracking?.currentLocation?.longitude ?? null}
        />
      </div>
      {tracking?.estimatedArrival && (
        <p className="mt-2 text-xs text-crust-500">
          Estimated arrival: {formatDate(tracking.estimatedArrival, "h:mm a")}
        </p>
      )}
    </section>
  );
}

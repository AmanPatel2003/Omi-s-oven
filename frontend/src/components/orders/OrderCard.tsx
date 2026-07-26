"use client";

import Image from "next/image";
import Link from "next/link";
import {
  useCancelOrderMutation,
  useReorderMutation,
} from "@/store/api/ordersApi";
import { OrderStatusBadge } from "@/components/orders/OrderStatusBadge";
import { Button } from "@/components/ui/Button";
import { formatCurrency, formatDate } from "@/lib/utils";
import type { Order } from "@/types/api";

export function OrderCard({ order }: { order: Order }) {
  const [cancelOrder, { isLoading: isCancelling }] = useCancelOrderMutation();
  const [reorder, { isLoading: isReordering }] = useReorderMutation();

  const canCancel = order.status === "pending" || order.status === "confirmed";

  return (
    <div className="rounded-xl border border-crust-100 bg-white p-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-crust-900">
            Order #{order.id.slice(-8)}
          </p>
          <p className="text-xs text-crust-500">
            {formatDate(order.createdAt)}
          </p>
        </div>
        <OrderStatusBadge status={order.status} />
      </div>

      <div className="mt-3 flex gap-2">
        {order.items.slice(0, 4).map((item, i) => (
          <div
            key={i}
            className="relative h-12 w-12 overflow-hidden rounded-lg bg-crust-50"
          >
            {item.image && (
              <Image
                src={item.image}
                alt={item.name}
                fill
                className="object-cover"
              />
            )}
          </div>
        ))}
        {order.items.length > 4 && (
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-crust-50 text-xs text-crust-500">
            +{order.items.length - 4}
          </div>
        )}
      </div>

      <div className="mt-3 flex items-center justify-between">
        <p className="text-sm font-semibold text-crust-900">
          {formatCurrency(order.total)}
        </p>
        <div className="flex gap-2">
          <Link href={`/orders/${order.id}`}>
            <Button variant="secondary" className="w-auto px-3 py-1.5 text-xs">
              Track
            </Button>
          </Link>
          {canCancel && (
            <Button
              variant="secondary"
              className="w-auto px-3 py-1.5 text-xs"
              isLoading={isCancelling}
              onClick={() => cancelOrder(order.id)}
            >
              Cancel
            </Button>
          )}
          <Button
            variant="secondary"
            className="w-auto px-3 py-1.5 text-xs"
            isLoading={isReordering}
            onClick={() => reorder(order.id)}
          >
            Reorder
          </Button>
        </div>
      </div>
    </div>
  );
}

"use client";

import { useTransitionOrderStatusMutation } from "@/store/api/adminOrdersApi";
import { ORDER_STATUS_LABELS } from "@/components/orders/OrderStatusBadge";
import { VALID_ORDER_TRANSITIONS, type OrderStatus } from "@/lib/constants";
import { Button } from "@/components/ui/Button";

export function StatusTransitionButton({
  orderId,
  currentStatus,
}: {
  orderId: string;
  currentStatus: OrderStatus;
}) {
  const [transitionStatus, { isLoading }] = useTransitionOrderStatusMutation();
  const nextStatuses = VALID_ORDER_TRANSITIONS[currentStatus];

  if (nextStatuses.length === 0) return null;

  return (
    <div className="flex gap-2">
      {nextStatuses.map((status) => (
        <Button
          key={status}
          variant={status === "cancelled" ? "secondary" : "primary"}
          className={
            status === "cancelled" ? "w-auto px-4 text-red-600" : "w-auto px-4"
          }
          isLoading={isLoading}
          onClick={() => transitionStatus({ id: orderId, status })}
        >
          Mark as {ORDER_STATUS_LABELS[status]}
        </Button>
      ))}
    </div>
  );
}

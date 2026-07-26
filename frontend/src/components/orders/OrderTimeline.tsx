import { cn, formatDate } from "@/lib/utils";
import { ORDER_STATUSES } from "@/lib/constants";
import type { OrderStatusHistoryEntry } from "@/types/api";

export function OrderTimeline({
  history,
}: {
  history: OrderStatusHistoryEntry[];
}) {
  const reachedStatuses = new Set(history.map((h) => h.status));
  const isCancelled = reachedStatuses.has("cancelled");
  const steps = isCancelled
    ? history.map((h) => h.status)
    : ORDER_STATUSES.filter((s) => s !== "cancelled");

  return (
    <ol className="flex flex-col gap-0">
      {steps.map((status, i) => {
        const entry = history.find((h) => h.status === status);
        const reached = !!entry;
        return (
          <li key={status} className="flex gap-3">
            <div className="flex flex-col items-center">
              <span
                className={cn(
                  "h-3 w-3 rounded-full",
                  reached ? "bg-crust-600" : "bg-crust-200",
                )}
              />
              {i < steps.length - 1 && (
                <span
                  className={cn(
                    "w-px flex-1",
                    reached ? "bg-crust-600" : "bg-crust-200",
                  )}
                />
              )}
            </div>
            <div className="pb-6">
              <p
                className={cn(
                  "text-sm font-medium",
                  reached ? "text-crust-900" : "text-crust-400",
                )}
              >
                {status.replace(/_/g, " ")}
              </p>
              {entry && (
                <p className="text-xs text-crust-500">
                  {formatDate(entry.timestamp, "d MMM, h:mm a")}
                </p>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}

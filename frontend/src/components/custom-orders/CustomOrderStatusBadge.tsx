import { cn } from "@/lib/utils";
import type { CustomOrderStatus } from "@/lib/constants";

const STATUS_STYLES: Record<CustomOrderStatus, string> = {
  pending: "bg-slate-100 text-slate-700",
  reviewing: "bg-indigo-100 text-indigo-700",
  quoted: "bg-teal-100 text-teal-700",
  confirmed: "bg-sky-100 text-sky-700",
  in_progress: "bg-orange-100 text-orange-700",
  completed: "bg-emerald-100 text-emerald-700",
  rejected: "bg-rose-100 text-rose-700",
  cancelled: "bg-stone-200 text-stone-600",
};

const STATUS_LABELS: Record<CustomOrderStatus, string> = {
  pending: "Pending Review",
  reviewing: "Under Review",
  quoted: "Quote Ready",
  confirmed: "Confirmed",
  in_progress: "In Progress",
  completed: "Completed",
  rejected: "Rejected",
  cancelled: "Cancelled",
};

export function CustomOrderStatusBadge({
  status,
}: {
  status: CustomOrderStatus;
}) {
  return (
    <span
      className={cn(
        "inline-block rounded-full px-2.5 py-0.5 text-xs font-medium",
        STATUS_STYLES[status],
      )}
    >
      {STATUS_LABELS[status]}
    </span>
  );
}

"use client";

import { useGetInventoryMovementsQuery } from "@/store/api/adminInventoryApi";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { cn, formatDate } from "@/lib/utils";

export default function InventoryMovementsPage({
  params,
}: {
  params: { id: string };
}) {
  const { data: movements, isLoading } = useGetInventoryMovementsQuery(
    params.id,
  );

  if (isLoading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="font-display text-2xl font-semibold text-crust-900">
        Movement History
      </h1>

      {!movements || movements.length === 0 ? (
        <p className="mt-8 text-center text-sm text-crust-500">
          No movements recorded yet.
        </p>
      ) : (
        <ol className="mt-6 flex flex-col gap-4">
          {movements.map((m) => (
            <li key={m.id} className="flex gap-3 border-b border-crust-50 pb-4">
              <span
                className={cn(
                  "mt-0.5 inline-block h-fit rounded-full px-2 py-0.5 text-xs font-medium",
                  m.type === "restock"
                    ? "bg-green-100 text-green-700"
                    : "bg-amber-100 text-amber-700",
                )}
              >
                {m.type === "restock" ? "Restock" : "Adjustment"}
              </span>
              <div>
                <p className="text-sm text-crust-800">
                  {m.quantity > 0 ? "+" : ""}
                  {m.quantity} — {m.reason}
                </p>
                <p className="text-xs text-crust-400">
                  {formatDate(m.createdAt, "d MMM yyyy, h:mm a")} ·{" "}
                  {m.performedBy}
                </p>
              </div>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}

import type { DeliveryPerformance } from "@/types/api";

export function DeliveryPerformanceCard({
  data,
}: {
  data: DeliveryPerformance;
}) {
  return (
    <div className="rounded-xl border border-crust-100 bg-white p-4">
      <p className="text-xs text-crust-500">Avg. delivery time</p>
      <p className="mt-1 text-2xl font-semibold text-crust-900">
        {data.avgDeliveryTimeMinutes != null
          ? `${data.avgDeliveryTimeMinutes} min`
          : "—"}
      </p>
      {data.note && <p className="mt-2 text-xs text-crust-500">{data.note}</p>}
    </div>
  );
}

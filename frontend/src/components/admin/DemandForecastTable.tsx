import { formatDate } from "@/lib/utils";
import type { ForecastRow } from "@/types/api";

export function DemandForecastTable({ rows }: { rows: ForecastRow[] }) {
  if (rows.length === 0) {
    return (
      <div className="rounded-xl border border-crust-100 bg-white p-6 text-center text-sm text-crust-500">
        No forecast data available.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-crust-100 bg-white">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-crust-100 bg-crust-50 text-left text-xs font-medium text-crust-500">
            <th className="px-3 py-2">Date</th>
            <th className="px-3 py-2 text-right">Predicted demand</th>
            <th className="px-3 py-2">Confidence</th>
          </tr>
        </thead>
        <tbody>
          {rows?.map((row) => (
            <tr
              key={row.date}
              className="border-b border-crust-50 last:border-0 align-top"
            >
              <td className="px-3 py-2">{formatDate(row.date)}</td>
              <td className="px-3 py-2 text-right font-medium text-crust-900">
                {row.predictedDemand}
              </td>
              <td className="px-3 py-2 text-xs text-crust-500">
                {row.confidenceNote}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

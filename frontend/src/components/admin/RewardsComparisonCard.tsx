import type { RewardsStats } from "@/types/api";

export function RewardsComparisonCard({ data }: { data: RewardsStats }) {
  const total = data.pointsIssued + data.pointsRedeemed;
  const redeemedPercent = total > 0 ? (data.pointsRedeemed / total) * 100 : 0;

  return (
    <div className="rounded-xl border border-crust-100 bg-white p-4">
      <p className="text-xs text-crust-500">Points issued vs. redeemed</p>
      <div className="mt-3 flex items-baseline justify-between text-sm">
        <span className="text-crust-700">
          Issued: {data.pointsIssued.toLocaleString()}
        </span>
        <span className="text-crust-700">
          Redeemed: {data.pointsRedeemed.toLocaleString()}
        </span>
      </div>
      <div className="mt-2 h-2 overflow-hidden rounded-full bg-crust-100">
        <div
          className="h-full rounded-full bg-crust-600"
          style={{ width: `${redeemedPercent}%` }}
        />
      </div>
    </div>
  );
}

"use client";

import { useAuth } from "@/hooks/useAuth";
import {
  useGetRewardsSummaryQuery,
  useGetRewardTransactionsQuery,
} from "@/store/api/rewardsApi";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { formatDate } from "@/lib/utils";

export function RewardsSummaryClient() {
  const { requireAuth, isHydrating } = useAuth();
  requireAuth();

  const { data: summary, isLoading } = useGetRewardsSummaryQuery();
  const { data: transactions } = useGetRewardTransactionsQuery();

  if (isHydrating || isLoading || !summary) {
    return (
      <div className="flex justify-center py-8">
        <LoadingSpinner />
      </div>
    );
  }

  const progressPercent =
    summary.pointsToNextTier > 0
      ? Math.min(
          100,
          (summary.pointsBalance /
            (summary.pointsBalance + summary.pointsToNextTier)) *
            100,
        )
      : 100;

  return (
    <div>
      <div className="rounded-xl border border-crust-100 bg-white p-5">
        <p className="text-sm text-crust-500">Points balance</p>
        <p className="text-3xl font-semibold text-crust-900">
          {summary.pointsBalance}
        </p>

        <div className="mt-4 flex items-center justify-between text-xs text-crust-600">
          <span className="font-medium">{summary.currentTier}</span>
          {summary.nextTier && (
            <span>
              {summary.pointsToNextTier} pts to {summary.nextTier}
            </span>
          )}
        </div>
        <div className="mt-2 h-2 overflow-hidden rounded-full bg-crust-100">
          <div
            className="h-full rounded-full bg-crust-600"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      <div className="mt-6">
        <h2 className="text-sm font-semibold text-crust-800">
          Transaction history
        </h2>
        <div className="mt-3 overflow-hidden rounded-xl border border-crust-100 bg-white">
          <table className="w-full text-sm">
            <tbody>
              {transactions && transactions.length > 0 ? (
                transactions.map((t) => (
                  <tr
                    key={t.id}
                    className="border-b border-crust-50 last:border-0"
                  >
                    <td className="p-3">
                      <p className="text-crust-800">{t.description}</p>
                      <p className="text-xs text-crust-400">
                        {formatDate(t.createdAt)}
                      </p>
                    </td>
                    <td
                      className={`p-3 text-right font-medium ${
                        t.type === "earned"
                          ? "text-green-700"
                          : "text-crust-600"
                      }`}
                    >
                      {t.type === "earned" ? "+" : "-"}
                      {t.points}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td className="p-4 text-center text-crust-500">
                    No transactions yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

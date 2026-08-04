"use client";

import { useState } from "react";
import {
  useGetRevenueByCategoryQuery,
  useGetCustomerGrowthQuery,
  useGetDeliveryPerformanceQuery,
  useGetRewardsStatsQuery,
  useGetDemandForecastQuery,
} from "@/store/api/adminAnalyticsApi";
import { DateRangePicker } from "@/components/admin/DateRangePicker";
import { RevenueByCategoryChart } from "@/components/admin/charts/RevenueByCategoryChart";
import { CustomerGrowthChart } from "@/components/admin/charts/CustomerGrowthChart";
import { ProductSalesChart } from "@/components/admin/charts/ProductSalesChart";
import { DeliveryPerformanceCard } from "@/components/admin/DeliveryPerformanceCard";
import { RewardsComparisonCard } from "@/components/admin/RewardsComparisonCard";
import { DemandForecastTable } from "@/components/admin/DemandForecastTable";
import { ExportButtons } from "@/components/admin/ExportButtons";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import type { AnalyticsDateRange } from "@/types/api";

const today = new Date().toISOString().slice(0, 10);
const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
  .toISOString()
  .slice(0, 10);

export default function AdminAnalyticsPage() {
  const [range, setRange] = useState<AnalyticsDateRange>({
    from: thirtyDaysAgo,
    to: today,
  });

  const { data: revenueByCategory, isLoading: isLoadingCategory } =
    useGetRevenueByCategoryQuery(range);
  const { data: customerGrowth, isLoading: isLoadingGrowth } =
    useGetCustomerGrowthQuery(range);
  const { data: deliveryPerformance } = useGetDeliveryPerformanceQuery(range);
  const { data: rewardsStats } = useGetRewardsStatsQuery(range);
  const { data: forecast } = useGetDemandForecastQuery();

  return (
    <div className="mx-auto max-w-6xl">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="font-display text-2xl font-semibold text-crust-900">
          Analytics
        </h1>
        <ExportButtons range={range} />
      </div>

      <div className="mt-4">
        <DateRangePicker range={range} onChange={setRange} />
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-crust-100 bg-white p-4">
          <p className="text-sm font-semibold text-crust-800">
            Revenue by category
          </p>
          <div className="mt-3">
            {isLoadingCategory ? (
              <div className="flex justify-center py-8">
                <LoadingSpinner />
              </div>
            ) : (
              <RevenueByCategoryChart data={revenueByCategory ?? []} />
            )}
          </div>
        </div>

        <div className="rounded-xl border border-crust-100 bg-white p-4">
          <p className="text-sm font-semibold text-crust-800">
            New vs. returning customers
          </p>
          <div className="mt-3">
            {isLoadingGrowth ? (
              <div className="flex justify-center py-8">
                <LoadingSpinner />
              </div>
            ) : (
              <CustomerGrowthChart data={customerGrowth ?? []} />
            )}
          </div>
        </div>
      </div>

      <div className="mt-6 rounded-xl border border-crust-100 bg-white p-4">
        <p className="text-sm font-semibold text-crust-800">
          Product sales over time
        </p>
        <div className="mt-3">
          <ProductSalesChart range={range} />
        </div>
      </div>

      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        {deliveryPerformance && (
          <DeliveryPerformanceCard data={deliveryPerformance} />
        )}
        {rewardsStats && <RewardsComparisonCard data={rewardsStats} />}
      </div>

      <div className="mt-6">
        <p className="mb-2 text-sm font-semibold text-crust-800">
          Demand forecast
        </p>
        <DemandForecastTable rows={forecast?.items ?? []} />
      </div>
    </div>
  );
}

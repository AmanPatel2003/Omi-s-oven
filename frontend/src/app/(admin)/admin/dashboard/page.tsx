"use client";

import Link from "next/link";
import {
  useGetDashboardStatsQuery,
  useGetDailySalesQuery,
  useGetMonthlySalesQuery,
  useGetHourlyHeatmapQuery,
  useGetTopProductsQuery,
  useGetLowStockAlertsQuery,
  useGetPendingOrdersQuery,
} from "@/store/api/adminDashboardApi";
import { StatCard } from "@/components/admin/StatCard";
import { DataTable } from "@/components/admin/DataTable";
import { HourlyHeatmap } from "@/components/admin/HourlyHeatmap";
import { DailySalesChart } from "@/components/admin/charts/DailySalesChart";
import { MonthlySalesChart } from "@/components/admin/charts/MonthlySalesChart";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { OrderStatusBadge } from "@/components/orders/OrderStatusBadge";
import { formatCurrency, formatDate } from "@/lib/utils";

export default function AdminDashboardPage() {
  const { data: stats, isLoading: isLoadingStats } =
    useGetDashboardStatsQuery();
  const { data: dailySales } = useGetDailySalesQuery();
  const { data: monthlySales } = useGetMonthlySalesQuery();
  const { data: heatmap } = useGetHourlyHeatmapQuery();
  const { data: topProducts } = useGetTopProductsQuery();
  const { data: lowStock } = useGetLowStockAlertsQuery();
  const { data: pendingOrders } = useGetPendingOrdersQuery();

  return (
    <div className="mx-auto max-w-6xl">
      <h1 className="font-display text-2xl font-semibold text-crust-900">
        Dashboard
      </h1>

      {isLoadingStats || !stats ? (
        <div className="mt-6 flex justify-center py-8">
          <LoadingSpinner />
        </div>
      ) : (
        <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
          <StatCard
            label="Today's revenue"
            value={formatCurrency(stats.todayRevenue)}
          />
          <StatCard label="Today's orders" value={String(stats.todayOrders)} />
          <StatCard label="New customers" value={String(stats.newCustomers)} />
          <StatCard
            label="Avg. order value"
            value={formatCurrency(stats.avgOrderValue)}
          />
        </div>
      )}

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-crust-100 bg-white p-4">
          <p className="text-sm font-semibold text-crust-800">Daily sales</p>
          <div className="mt-3">
            <DailySalesChart data={dailySales ?? []} />
          </div>
        </div>
        <div className="rounded-xl border border-crust-100 bg-white p-4">
          <p className="text-sm font-semibold text-crust-800">Monthly sales</p>
          <div className="mt-3">
            <MonthlySalesChart data={monthlySales ?? []} />
          </div>
        </div>
      </div>

      <div className="mt-6 rounded-xl border border-crust-100 bg-white p-4">
        <p className="text-sm font-semibold text-crust-800">
          Orders by day &amp; hour
        </p>
        <div className="mt-3">
          <HourlyHeatmap cells={heatmap ?? []} />
        </div>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <div>
          <p className="mb-2 text-sm font-semibold text-crust-800">
            Top products
          </p>
          <DataTable
            rows={topProducts ?? []}
            emptyMessage="No sales data yet."
            columns={[
              { header: "Product", render: (p) => p.name },
              {
                header: "Units sold",
                render: (p) => p.unitsSold,
                align: "right",
              },
              {
                header: "Revenue",
                render: (p) => formatCurrency(p.revenue),
                align: "right",
              },
            ]}
          />
        </div>

        <div>
          <p className="mb-2 text-sm font-semibold text-crust-800">
            Low stock alerts
          </p>
          <DataTable
            rows={lowStock ?? []}
            emptyMessage="Nothing running low."
            rowHref={(item) => `/admin/products/${item.id}/edit`}
            columns={[
              { header: "Product", render: (p) => p.name },
              { header: "Stock", render: (p) => p.stock, align: "right" },
              {
                header: "Threshold",
                render: (p) => p.threshold,
                align: "right",
              },
            ]}
          />
        </div>
      </div>

      <div className="mt-6">
        <p className="mb-2 text-sm font-semibold text-crust-800">
          Pending orders
        </p>
        <DataTable
          rows={pendingOrders ?? []}
          emptyMessage="No pending orders."
          rowHref={(order) => `/admin/orders/${order.id}`}
          columns={[
            { header: "Order", render: (o) => `#${o.id.slice(-8)}` },
            { header: "Customer", render: (o) => o.customerName },
            {
              header: "Status",
              render: (o) => <OrderStatusBadge status={o.status} />,
            },
            { header: "Placed", render: (o) => formatDate(o.createdAt) },
            {
              header: "Total",
              render: (o) => formatCurrency(o.total),
              align: "right",
            },
          ]}
        />
      </div>
    </div>
  );
}

"use client";

import { useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { useGetProductsQuery } from "@/store/api/productsApi";
import { useGetProductSalesQuery } from "@/store/api/adminAnalyticsApi";
import { formatDate } from "@/lib/utils";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import type { AnalyticsDateRange } from "@/types/api";

export function ProductSalesChart({ range }: { range: AnalyticsDateRange }) {
  const { data: products } = useGetProductsQuery({ pageSize: 100 });
  const [productId, setProductId] = useState<string>("");

  const { data: sales, isLoading } = useGetProductSalesQuery(
    { productId, ...range },
    { skip: !productId },
  );

  return (
    <div>
      <select
        value={productId}
        onChange={(e) => setProductId(e.target.value)}
        className="rounded-xl border border-crust-200 px-3 py-2 text-sm"
      >
        <option value="">Select a product…</option>
        {products?.items.map((p) => (
          <option key={p.id} value={p.id}>
            {p.name}
          </option>
        ))}
      </select>

      <div className="mt-4">
        {!productId ? (
          <p className="py-8 text-center text-sm text-crust-500">
            Pick a product to see its sales over time.
          </p>
        ) : isLoading ? (
          <div className="flex justify-center py-8">
            <LoadingSpinner />
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={sales ?? []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F4E9D6" />
              <XAxis
                dataKey="date"
                tickFormatter={(d) => formatDate(d, "d MMM")}
                tick={{ fontSize: 11 }}
              />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip labelFormatter={(d) => formatDate(d as string)} />
              <Line
                type="monotone"
                dataKey="unitsSold"
                stroke="#8A5824"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}

"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { formatCurrency } from "@/lib/utils";
import type { RevenueByCategory } from "@/types/api";

export function RevenueByCategoryChart({
  data,
}: {
  data: RevenueByCategory[];
}) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data} layout="vertical">
        <CartesianGrid strokeDasharray="3 3" stroke="#F4E9D6" />
        <XAxis
          type="number"
          tickFormatter={(v) => formatCurrency(v)}
          tick={{ fontSize: 11 }}
        />
        <YAxis
          type="category"
          dataKey="category"
          tick={{ fontSize: 11 }}
          width={100}
        />
        <Tooltip formatter={(value: number) => formatCurrency(value)} />
        <Bar dataKey="revenue" fill="#A9702F" radius={[0, 4, 4, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

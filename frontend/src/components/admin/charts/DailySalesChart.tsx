"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { formatCurrency, formatDate } from "@/lib/utils";
import type { SalesPoint } from "@/types/api";

export function DailySalesChart({ data }: { data: SalesPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#F4E9D6" />
        <XAxis
          dataKey="date"
          tickFormatter={(d) => formatDate(d, "d MMM")}
          tick={{ fontSize: 11 }}
        />
        <YAxis
          tickFormatter={(v) => formatCurrency(v)}
          tick={{ fontSize: 11 }}
          width={70}
        />
        <Tooltip
          formatter={(value: number) => formatCurrency(value)}
          labelFormatter={(d) => formatDate(d as string)}
        />
        <Line
          type="monotone"
          dataKey="revenue"
          stroke="#8A5824"
          strokeWidth={2}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

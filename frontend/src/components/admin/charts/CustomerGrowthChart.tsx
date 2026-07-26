"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { formatDate } from "@/lib/utils";
import type { CustomerGrowthPoint } from "@/types/api";

export function CustomerGrowthChart({ data }: { data: CustomerGrowthPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <AreaChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#F4E9D6" />
        <XAxis
          dataKey="date"
          tickFormatter={(d) => formatDate(d, "d MMM")}
          tick={{ fontSize: 11 }}
        />
        <YAxis tick={{ fontSize: 11 }} />
        <Tooltip labelFormatter={(d) => formatDate(d as string)} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Area
          type="monotone"
          dataKey="newCustomers"
          name="New"
          stackId="1"
          stroke="#8A5824"
          fill="#D6AE72"
        />
        <Area
          type="monotone"
          dataKey="returningCustomers"
          name="Returning"
          stackId="1"
          stroke="#4D2F15"
          fill="#A9702F"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

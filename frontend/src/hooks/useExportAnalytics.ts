"use client";

import { useState } from "react";
import { useAppSelector } from "@/store/hooks";
import type { AnalyticsDateRange, ExportFormat } from "@/types/api";

export function useExportAnalytics() {
  const accessToken = useAppSelector((state) => state.auth.accessToken);
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function exportAnalytics(
    format: ExportFormat,
    range: AnalyticsDateRange,
  ) {
    setError(null);
    setIsExporting(true);
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/admin/analytics/export?format=${format}&from=${range.from}&to=${range.to}`,
        {
          headers: accessToken
            ? { Authorization: `Bearer ${accessToken}` }
            : {},
        },
      );
      if (!res.ok) throw new Error("Export failed");

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `analytics-${range.from}-to-${range.to}.${format === "excel" ? "xlsx" : "pdf"}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch {
      setError("Couldn't generate the export. Please try again.");
    } finally {
      setIsExporting(false);
    }
  }

  return { exportAnalytics, isExporting, error };
}

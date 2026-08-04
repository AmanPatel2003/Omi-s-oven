"use client";

import { useState } from "react";
import { useAppSelector } from "@/store/hooks";

export function useExportOrdersCsv() {
  const access_token = useAppSelector((state) => state.auth.access_token);
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function exportOrdersCsv(range: { from?: string; to?: string }) {
    setError(null);
    setIsExporting(true);
    try {
      const params = new URLSearchParams();
      if (range.from) params.set("from", range.from);
      if (range.to) params.set("to", range.to);
      const res = await fetch(
        // `${process.env.NEXT_PUBLIC_API_URL}/admin/orders/export?${params.toString()}`,
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/admin/orders/export?${params.toString()}`,
        {
          headers: access_token
            ? { Authorization: `Bearer ${access_token}` }
            : {},
        },
      );
      if (!res.ok) throw new Error("Export failed");

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `orders${range.from ? `-${range.from}-to-${range.to}` : ""}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch {
      setError("Couldn't export orders. Please try again.");
    } finally {
      setIsExporting(false);
    }
  }

  return { exportOrdersCsv, isExporting, error };
}

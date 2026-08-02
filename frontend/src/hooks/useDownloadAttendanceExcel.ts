"use client";

import { useState } from "react";
import { useAppSelector } from "@/store/hooks";

export function useDownloadAttendanceExcel() {
  const access_token = useAppSelector((state) => state.auth.access_token);
  const [isDownloading, setIsDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function downloadExcel(month: string) {
    setError(null);
    setIsDownloading(true);
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/admin/attendance/export?month=${month}`,
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
      a.download = `attendance-${month}.xlsx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch {
      setError("Couldn't export attendance. Please try again.");
    } finally {
      setIsDownloading(false);
    }
  }

  return { downloadExcel, isDownloading, error };
}

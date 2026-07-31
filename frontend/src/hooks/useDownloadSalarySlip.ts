"use client";

import { useState } from "react";
import { useAppSelector } from "@/store/hooks";

export function useDownloadSalarySlip() {
  const accessToken = useAppSelector((state) => state.auth.accessToken);
  const [isDownloading, setIsDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function downloadSlip(staffId: string, month: string) {
    setError(null);
    setIsDownloading(true);
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/admin/salary/slip/${staffId}?month=${month}`,
        {
          headers: accessToken
            ? { Authorization: `Bearer ${accessToken}` }
            : {},
        },
      );
      if (!res.ok) throw new Error("Slip generation failed");

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      window.open(url, "_blank");
    } catch {
      setError("Couldn't generate the salary slip. Please try again.");
    } finally {
      setIsDownloading(false);
    }
  }

  return { downloadSlip, isDownloading, error };
}

"use client";

import { useExportAnalytics } from "@/hooks/useExportAnalytics";
import { Button } from "@/components/ui/Button";
import type { AnalyticsDateRange } from "@/types/api";

export function ExportButtons({ range }: { range: AnalyticsDateRange }) {
  const { exportAnalytics, isExporting, error } = useExportAnalytics();

  return (
    <div className="flex items-center gap-2">
      <Button
        variant="secondary"
        className="w-auto px-3 py-1.5 text-xs"
        isLoading={isExporting}
        onClick={() => exportAnalytics("excel", range)}
      >
        Export Excel
      </Button>
      <Button
        variant="secondary"
        className="w-auto px-3 py-1.5 text-xs"
        isLoading={isExporting}
        onClick={() => exportAnalytics("pdf", range)}
      >
        Export PDF
      </Button>
      {error && <span className="text-xs text-red-600">{error}</span>}
    </div>
  );
}

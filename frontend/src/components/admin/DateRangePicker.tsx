"use client";

import type { AnalyticsDateRange } from "@/types/api";

export function DateRangePicker({
  range,
  onChange,
}: {
  range: AnalyticsDateRange;
  onChange: (range: AnalyticsDateRange) => void;
}) {
  return (
    <div className="flex items-center gap-3">
      <label className="flex items-center gap-2 text-sm text-crust-700">
        From
        <input
          type="date"
          value={range.from}
          max={range.to}
          onChange={(e) => onChange({ ...range, from: e.target.value })}
          className="rounded-lg border border-crust-200 px-2 py-1.5 text-sm"
        />
      </label>
      <label className="flex items-center gap-2 text-sm text-crust-700">
        To
        <input
          type="date"
          value={range.to}
          min={range.from}
          max={new Date().toISOString().slice(0, 10)}
          onChange={(e) => onChange({ ...range, to: e.target.value })}
          className="rounded-lg border border-crust-200 px-2 py-1.5 text-sm"
        />
      </label>
    </div>
  );
}

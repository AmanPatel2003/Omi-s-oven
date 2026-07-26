import { cn } from "@/lib/utils";
import type { HeatmapCell } from "@/types/api";

const DAY_LABELS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

const INTENSITY_CLASSES = [
  "bg-crust-50",
  "bg-crust-100",
  "bg-crust-200",
  "bg-crust-400",
  "bg-crust-600",
  "bg-crust-800",
];

export function HourlyHeatmap({ cells }: { cells: HeatmapCell[] }) {
  const maxValue = Math.max(1, ...cells.map((c) => c.value));
  const valueByKey = new Map(
    cells.map((c) => [`${c.dayOfWeek}-${c.hour}`, c.value]),
  );

  function intensityClass(value: number) {
    const bucket = Math.min(
      INTENSITY_CLASSES.length - 1,
      Math.floor((value / maxValue) * (INTENSITY_CLASSES.length - 1)),
    );
    return INTENSITY_CLASSES[bucket];
  }

  return (
    <div className="overflow-x-auto">
      <div className="inline-grid grid-cols-[auto_repeat(24,1fr)] gap-[2px]">
        <div />
        {Array.from({ length: 24 }, (_, hour) => (
          <div key={hour} className="text-center text-[9px] text-crust-400">
            {hour % 3 === 0 ? hour : ""}
          </div>
        ))}

        {DAY_LABELS.map((label, dayOfWeek) => (
          <div key={label} className="contents">
            <div className="pr-2 text-right text-xs text-crust-500">
              {label}
            </div>
            {Array.from({ length: 24 }, (_, hour) => {
              const value = valueByKey.get(`${dayOfWeek}-${hour}`) ?? 0;
              return (
                <div
                  key={hour}
                  title={`${label} ${hour}:00 — ${value}`}
                  className={cn("h-4 w-4 rounded-sm", intensityClass(value))}
                />
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}

"use client";

import { useGetMyAttendanceQuery } from "@/store/api/staffApi";
import { ATTENDANCE_STATUS_STYLES } from "@/components/admin/AttendanceGrid";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { cn, formatDate } from "@/lib/utils";

export default function StaffAttendancePage() {
  const { data: days, isLoading } = useGetMyAttendanceQuery();

  if (isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  const byDate = new Map((days ?? []).map((d) => [d.date, d.status]));
  const now = new Date();
  const year = now.getFullYear();
  const month = now.getMonth();
  const firstDay = new Date(year, month, 1);
  const totalDays = new Date(year, month + 1, 0).getDate();
  const leadingBlanks = firstDay.getDay();

  const cells: (number | null)[] = [
    ...Array(leadingBlanks).fill(null),
    ...Array.from({ length: totalDays }, (_, i) => i + 1),
  ];

  return (
    <div className="mx-auto max-w-md px-4 py-6">
      <h1 className="font-display text-2xl font-semibold text-crust-900">
        Attendance — {formatDate(now.toISOString(), "MMMM yyyy")}
      </h1>

      <div className="mt-4 grid grid-cols-7 gap-1.5 text-center text-xs">
        {["S", "M", "T", "W", "T", "F", "S"].map((d, i) => (
          <div key={i} className="font-medium text-crust-400">
            {d}
          </div>
        ))}
        {cells.map((day, i) => {
          if (day == null) return <div key={i} />;
          const dateKey = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
          const status = byDate.get(dateKey);
          return (
            <div
              key={i}
              className={cn(
                "flex aspect-square items-center justify-center rounded-lg text-sm",
                status
                  ? ATTENDANCE_STATUS_STYLES[status]
                  : "bg-crust-50 text-crust-400",
              )}
            >
              {day}
            </div>
          );
        })}
      </div>

      <div className="mt-4 flex flex-wrap gap-3 text-xs text-crust-600">
        <Legend label="Present" className={ATTENDANCE_STATUS_STYLES.present} />
        <Legend label="Absent" className={ATTENDANCE_STATUS_STYLES.absent} />
        <Legend label="Leave" className={ATTENDANCE_STATUS_STYLES.leave} />
        <Legend label="Holiday" className={ATTENDANCE_STATUS_STYLES.holiday} />
      </div>
    </div>
  );
}

function Legend({ label, className }: { label: string; className: string }) {
  return (
    <span className="flex items-center gap-1.5">
      <span className={cn("h-3 w-3 rounded", className)} />
      {label}
    </span>
  );
}

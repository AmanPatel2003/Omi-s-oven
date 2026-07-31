"use client";

import { useState } from "react";
import {
  useGetTodayAttendanceQuery,
  useGetAttendanceReportQuery,
  useClockInStaffMutation,
  useClockOutStaffMutation,
} from "@/store/api/adminAttendanceApi";
import { useDownloadAttendanceExcel } from "@/hooks/useDownloadAttendanceExcel";
import {
  AttendanceGrid,
  ATTENDANCE_STATUS_STYLES,
} from "@/components/admin/AttendanceGrid";
import { MarkLeaveModal } from "@/components/admin/MarkLeaveModal";
import { Button } from "@/components/ui/Button";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { cn } from "@/lib/utils";
import type { TodayAttendanceEntry } from "@/types/api";

type Tab = "today" | "monthly";

function daysInMonth(month: string): number {
  const parts = month.split("-");

  if (parts.length !== 2) {
    throw new Error("Invalid month format. Expected YYYY-MM");
  }

  const year = Number(parts[0]);
  const m = Number(parts[1]);

  return new Date(year, m, 0).getDate();
}

export default function AdminAttendancePage() {
  const [tab, setTab] = useState<Tab>("today");
  const [month, setMonth] = useState(new Date().toISOString().slice(0, 7));
  const [leaveTarget, setLeaveTarget] = useState<TodayAttendanceEntry | null>(
    null,
  );

  const { data: today, isLoading: isLoadingToday } = useGetTodayAttendanceQuery(
    undefined,
    {
      skip: tab !== "today",
      pollingInterval: tab === "today" ? 30_000 : undefined,
    },
  );
  const { data: report, isLoading: isLoadingReport } =
    useGetAttendanceReportQuery(month, { skip: tab !== "monthly" });

  const [clockIn] = useClockInStaffMutation();
  const [clockOut] = useClockOutStaffMutation();
  const { downloadExcel, isDownloading } = useDownloadAttendanceExcel();

  return (
    <div className="mx-auto max-w-5xl">
      <h1 className="font-display text-2xl font-semibold text-crust-900">
        Attendance
      </h1>

      <div className="mt-4 flex gap-2">
        <TabButton
          label="Today"
          active={tab === "today"}
          onClick={() => setTab("today")}
        />
        <TabButton
          label="Monthly Report"
          active={tab === "monthly"}
          onClick={() => setTab("monthly")}
        />
      </div>

      {tab === "today" ? (
        <div className="mt-4">
          {isLoadingToday ? (
            <div className="flex justify-center py-8">
              <LoadingSpinner />
            </div>
          ) : (
            <div className="overflow-hidden rounded-xl border border-crust-100 bg-white">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-crust-100 bg-crust-50 text-left text-xs font-medium text-crust-500">
                    <th className="px-3 py-2">Staff</th>
                    <th className="px-3 py-2">Status</th>
                    <th className="px-3 py-2">Clock in</th>
                    <th className="px-3 py-2">Clock out</th>
                    <th className="px-3 py-2">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {today?.map((entry) => (
                    <tr
                      key={entry.staffId}
                      className="border-b border-crust-50 last:border-0"
                    >
                      <td className="px-3 py-2">{entry.staffName}</td>
                      <td className="px-3 py-2">
                        <span
                          className={cn(
                            "rounded-full px-2 py-0.5 text-xs font-medium",
                            ATTENDANCE_STATUS_STYLES[entry.status],
                          )}
                        >
                          {entry.status}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-crust-600">
                        {entry.clockIn ?? "—"}
                      </td>
                      <td className="px-3 py-2 text-crust-600">
                        {entry.clockOut ?? "—"}
                      </td>
                      <td className="px-3 py-2">
                        <div className="flex gap-3 text-xs">
                          <button
                            type="button"
                            disabled={!!entry.clockIn}
                            onClick={() => clockIn(entry.staffId)}
                            className="text-crust-600 underline disabled:text-crust-300"
                          >
                            Clock in
                          </button>
                          <button
                            type="button"
                            disabled={!entry.clockIn || !!entry.clockOut}
                            onClick={() => clockOut(entry.staffId)}
                            className="text-crust-600 underline disabled:text-crust-300"
                          >
                            Clock out
                          </button>
                          <button
                            type="button"
                            onClick={() => setLeaveTarget(entry)}
                            className="text-crust-600 underline"
                          >
                            Mark leave
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ) : (
        <div className="mt-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <input
              type="month"
              value={month}
              onChange={(e) => setMonth(e.target.value)}
              className="rounded-xl border border-crust-200 px-3 py-2 text-sm"
            />
            <Button
              variant="secondary"
              className="w-auto px-4"
              isLoading={isDownloading}
              onClick={() => downloadExcel(month)}
            >
              Export Excel
            </Button>
          </div>

          <div className="mt-4">
            {isLoadingReport ? (
              <div className="flex justify-center py-8">
                <LoadingSpinner />
              </div>
            ) : (
              <AttendanceGrid
                rows={report ?? []}
                daysInMonth={daysInMonth(month)}
              />
            )}
          </div>
        </div>
      )}

      {leaveTarget && (
        <MarkLeaveModal
          staff={leaveTarget}
          onClose={() => setLeaveTarget(null)}
        />
      )}
    </div>
  );
}

function TabButton({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "rounded-full px-3 py-1.5 text-sm font-medium",
        active ? "bg-crust-600 text-white" : "bg-crust-100 text-crust-600",
      )}
    >
      {label}
    </button>
  );
}

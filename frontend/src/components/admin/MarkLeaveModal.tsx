"use client";

import { useState } from "react";
import { useMarkLeaveMutation } from "@/store/api/adminAttendanceApi";
import { Button } from "@/components/ui/Button";
import type { TodayAttendanceEntry } from "@/types/api";

export function MarkLeaveModal({
  staff,
  onClose,
}: {
  staff: TodayAttendanceEntry;
  onClose: () => void;
}) {
  const [markLeave, { isLoading }] = useMarkLeaveMutation();
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [reason, setReason] = useState("");

  async function handleSubmit() {
    if (!startDate || !endDate) return;
    await markLeave({
      staff_id: staff.staff_id,
      start_date: startDate,
      end_date: endDate,
      reason: reason || undefined,
    });
    onClose();
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4">
      <div className="w-full max-w-sm rounded-xl bg-white p-5">
        <p className="font-medium text-crust-900">
          Mark leave — {staff.staff_name}
        </p>

        <div className="mt-4 flex flex-col gap-3">
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium text-crust-800">From</label>
              <input
                type="date"
                value={startDate}
                max={endDate || undefined}
                onChange={(e) => setStartDate(e.target.value)}
                className="rounded-lg border border-crust-200 px-3 py-2 text-sm"
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium text-crust-800">To</label>
              <input
                type="date"
                value={endDate}
                min={startDate || undefined}
                onChange={(e) => setEndDate(e.target.value)}
                className="rounded-lg border border-crust-200 px-3 py-2 text-sm"
              />
            </div>
          </div>
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-crust-800">
              Reason (optional)
            </label>
            <input
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="rounded-lg border border-crust-200 px-3 py-2 text-sm"
            />
          </div>
        </div>

        <div className="mt-5 flex justify-end gap-3">
          <Button variant="secondary" className="w-auto px-4" onClick={onClose}>
            Cancel
          </Button>
          <Button
            className="w-auto px-4"
            isLoading={isLoading}
            disabled={!startDate || !endDate}
            onClick={handleSubmit}
          >
            Mark Leave
          </Button>
        </div>
      </div>
    </div>
  );
}

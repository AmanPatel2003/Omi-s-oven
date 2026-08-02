"use client";

import {
  useGetClockStatusQuery,
  useClockInMutation,
  useClockOutMutation,
  useGetAssignedOrdersQuery,
} from "@/store/api/staffApi";
import { Button } from "@/components/ui/Button";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { formatDate } from "@/lib/utils";

export default function StaffDashboardPage() {
  const { data: status, isLoading: isLoadingStatus } = useGetClockStatusQuery();
  const [clockIn, { isLoading: isClockingIn }] = useClockInMutation();
  const [clockOut, { isLoading: isClockingOut }] = useClockOutMutation();
  const { data: assigned } = useGetAssignedOrdersQuery();

  const todayCount = assigned?.length ?? 0;

  return (
    <div className="mx-auto max-w-md px-4 py-6">
      <h1 className="font-display text-2xl font-semibold text-crust-900">
        Dashboard
      </h1>

      {isLoadingStatus ? (
        <div className="mt-8 flex justify-center">
          <LoadingSpinner />
        </div>
      ) : (
        <div className="mt-6 rounded-2xl border border-crust-100 bg-white p-6 text-center">
          <p className="text-sm text-crust-500">
            {status?.isClockedIn && status.clockInTime
              ? `Clocked in since ${formatDate(status.clockInTime, "h:mm a")}`
              : "Not clocked in"}
          </p>

          <Button
            className={
              status?.isClockedIn
                ? "mt-4 h-16 bg-crust-800 text-lg hover:bg-crust-900"
                : "mt-4 h-16 text-lg"
            }
            isLoading={isClockingIn || isClockingOut}
            onClick={() => (status?.isClockedIn ? clockOut() : clockIn())}
          >
            {status?.isClockedIn ? "Clock Out" : "Clock In"}
          </Button>
        </div>
      )}

      <div className="mt-4 rounded-2xl border border-crust-100 bg-white p-4 text-center">
        <p className="text-3xl font-semibold text-crust-900">{todayCount}</p>
        <p className="text-sm text-crust-500">
          {todayCount === 1
            ? "delivery assigned today"
            : "deliveries assigned today"}
        </p>
      </div>
    </div>
  );
}

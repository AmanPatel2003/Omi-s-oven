"use client";

import { useGetMySalaryQuery } from "@/store/api/staffApi";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { formatCurrency, formatDate } from "@/lib/utils";

export default function StaffSalaryPage() {
  const { data: slips, isLoading } = useGetMySalaryQuery();

  if (isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-md px-4 py-6">
      <h1 className="font-display text-2xl font-semibold text-crust-900">
        Salary
      </h1>

      {!slips || slips.length === 0 ? (
        <p className="mt-8 text-center text-sm text-crust-500">
          No salary slips yet.
        </p>
      ) : (
        <div className="mt-4 flex flex-col gap-2">
          {slips.map((slip) => (
            <div
              key={slip.id}
              className="flex items-center justify-between rounded-xl border border-crust-100 bg-white p-4"
            >
              <div>
                <p className="text-sm font-medium text-crust-900">
                  {slip.month}
                </p>
                <p className="text-xs text-crust-500">
                  Paid {formatDate(slip.paymentDate)}
                </p>
              </div>
              <p className="text-sm font-semibold text-crust-900">
                {formatCurrency(slip.netPaid)}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

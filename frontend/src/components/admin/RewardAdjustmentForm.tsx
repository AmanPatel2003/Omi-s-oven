"use client";

import { useState } from "react";
import { useAdjustCustomerRewardPointsMutation } from "@/store/api/adminCustomersApi";
import { Button } from "@/components/ui/Button";

export function RewardAdjustmentForm({ customerId }: { customerId: string }) {
  const [adjustPoints, { isLoading }] = useAdjustCustomerRewardPointsMutation();
  const [points, setPoints] = useState(0);
  const [reason, setReason] = useState("");
  const [success, setSuccess] = useState(false);

  async function handleSubmit() {
    if (points === 0 || !reason.trim()) return;
    setSuccess(false);
    await adjustPoints({ id: customerId, points, reason });
    setSuccess(true);
    setPoints(0);
    setReason("");
  }

  return (
    <div className="rounded-xl border border-crust-100 bg-white p-4">
      <p className="text-sm font-semibold text-crust-800">Manual Adjustment</p>
      <p className="mt-1 text-xs text-crust-500">
        Directly credits or debits this customer's reward points balance.
      </p>

      <div className="mt-3 flex flex-col gap-3">
        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-medium text-crust-800">
            Points (+/-)
          </label>
          <input
            type="number"
            value={points}
            onChange={(e) => setPoints(Number(e.target.value))}
            className="rounded-lg border border-crust-200 px-3 py-2 text-sm"
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-medium text-crust-800">Reason</label>
          <input
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="e.g. Goodwill credit for late delivery"
            className="rounded-lg border border-crust-200 px-3 py-2 text-sm"
          />
        </div>
        {success && (
          <p className="text-xs text-green-700">Adjustment applied.</p>
        )}
        <Button
          variant="secondary"
          className="w-fit"
          isLoading={isLoading}
          disabled={points === 0 || !reason.trim()}
          onClick={handleSubmit}
        >
          Apply Manual Adjustment
        </Button>
      </div>
    </div>
  );
}

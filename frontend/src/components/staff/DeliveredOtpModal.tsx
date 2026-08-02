"use client";

import { useState } from "react";
import { useMarkDeliveredMutation } from "@/store/api/staffApi";
import { Button } from "@/components/ui/Button";

export function DeliveredOtpModal({
  orderId,
  onClose,
}: {
  orderId: string;
  onClose: () => void;
}) {
  const [markDelivered, { isLoading }] = useMarkDeliveredMutation();
  const [otp, setOtp] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit() {
    if (otp.trim().length === 0) return;
    setError(null);
    try {
      await markDelivered({ orderId, otp: otp.trim() }).unwrap();
      onClose();
    } catch {
      setError("That code didn't match. Ask the customer to double-check it.");
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/30 sm:items-center">
      <div className="w-full max-w-sm rounded-t-2xl bg-white p-5 sm:rounded-2xl">
        <p className="font-medium text-crust-900">Confirm delivery</p>
        <p className="mt-1 text-sm text-crust-500">
          Ask the customer for their delivery code.
        </p>

        <input
          inputMode="numeric"
          autoFocus
          value={otp}
          onChange={(e) => setOtp(e.target.value)}
          placeholder="Enter code"
          className="mt-4 w-full rounded-xl border border-crust-200 px-4 py-3 text-center text-lg tracking-widest"
        />
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}

        <div className="mt-4 flex gap-3">
          <Button variant="secondary" className="flex-1" onClick={onClose}>
            Cancel
          </Button>
          <Button
            className="flex-1"
            isLoading={isLoading}
            disabled={!otp.trim()}
            onClick={handleSubmit}
          >
            Confirm
          </Button>
        </div>
      </div>
    </div>
  );
}

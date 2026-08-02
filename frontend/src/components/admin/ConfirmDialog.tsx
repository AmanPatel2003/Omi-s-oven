"use client";

import { Button } from "@/components/ui/Button";

export function ConfirmDialog({
  title,
  description,
  confirmLabel = "Confirm",
  isDangerous,
  isLoading,
  onConfirm,
  onCancel,
}: {
  title: string;
  description: React.ReactNode;
  confirmLabel?: string;
  isDangerous?: boolean;
  isLoading?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4">
      <div className="w-full max-w-sm rounded-xl bg-white p-5">
        <p className="font-medium text-crust-900">{title}</p>
        <div className="mt-2 text-sm text-crust-600">{description}</div>
        <div className="mt-5 flex justify-end gap-3">
          <Button
            variant="secondary"
            className="w-auto px-4"
            onClick={onCancel}
          >
            Cancel
          </Button>
          <Button
            className={
              isDangerous
                ? "w-auto bg-red-600 px-4 hover:bg-red-700"
                : "w-auto px-4"
            }
            isLoading={isLoading}
            onClick={onConfirm}
          >
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  );
}

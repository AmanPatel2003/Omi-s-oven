"use client";

import { useEffect } from "react";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { dismissToast } from "@/store/slices/uiSlice";
import { cn } from "@/lib/utils";

const AUTO_DISMISS_MS = 4000;

const VARIANT_STYLES = {
  success: "bg-green-50 border-green-200 text-green-800",
  error: "bg-red-50 border-red-200 text-red-800",
  info: "bg-crust-50 border-crust-200 text-crust-800",
};

export function ToastContainer() {
  const toasts = useAppSelector((state) => state.ui.toasts);

  return (
    <div
      className="fixed bottom-4 right-4 z-[100] flex w-full max-w-sm flex-col gap-2 sm:bottom-6 sm:right-6"
      aria-live="polite"
    >
      {toasts.map((toast) => (
        <ToastItem
          key={toast.id}
          id={toast.id}
          message={toast.message}
          variant={toast.variant}
        />
      ))}
    </div>
  );
}

function ToastItem({
  id,
  message,
  variant,
}: {
  id: string;
  message: string;
  variant: "success" | "error" | "info";
}) {
  const dispatch = useAppDispatch();

  useEffect(() => {
    const timer = setTimeout(() => dispatch(dismissToast(id)), AUTO_DISMISS_MS);
    return () => clearTimeout(timer);
  }, [id, dispatch]);

  return (
    <div
      role="status"
      className={cn(
        "flex items-start justify-between gap-3 rounded-xl border px-4 py-3 text-sm shadow-lg",
        VARIANT_STYLES[variant],
      )}
    >
      <span>{message}</span>
      <button
        type="button"
        onClick={() => dispatch(dismissToast(id))}
        aria-label="Dismiss"
        className="text-current opacity-60 hover:opacity-100"
      >
        ✕
      </button>
    </div>
  );
}

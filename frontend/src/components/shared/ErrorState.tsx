"use client";

import type { SerializedError } from "@reduxjs/toolkit";
import type { FetchBaseQueryError } from "@reduxjs/toolkit/query";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";

type QueryError = FetchBaseQueryError | SerializedError | undefined;

export function getErrorMessage(error: QueryError): string {
  if (!error) return "Something went wrong. Please try again.";

  if ("status" in error) {
    const status = error.status;
    if (typeof status === "number") {
      if (status >= 500) {
        return "Something went wrong on our end. Please try again in a moment.";
      }
      const data = error.data as { message?: string } | undefined;
      if (data?.message) return data.message;
      return "That didn't go through — please check and try again.";
    }
    return "Couldn't connect. Check your internet connection and try again.";
  }

  return "Something went wrong. Please try again.";
}

export function ErrorState({
  error,
  onRetry,
  className,
}: {
  error: QueryError;
  onRetry?: () => void;
  className?: string;
}) {
  const message = getErrorMessage(error);

  return (
    <div
      role="alert"
      className={cn(
        "flex flex-col items-center gap-3 rounded-xl border border-crust-100 bg-white p-6 text-center",
        className,
      )}
    >
      <p className="text-sm text-crust-600">{message}</p>
      {onRetry && (
        <Button variant="secondary" className="w-auto px-4" onClick={onRetry}>
          Try again
        </Button>
      )}
    </div>
  );
}

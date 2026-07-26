"use client";

import { useAuth } from "@/hooks/useAuth";
import { CustomOrderForm } from "@/components/forms/CustomOrderForm";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";

export default function NewCustomOrderPage() {
  const { requireAuth, isHydrating } = useAuth();
  requireAuth();

  if (isHydrating) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-xl px-4 py-8">
      <h1 className="font-display text-2xl font-semibold text-crust-900">
        Request a Custom Cake
      </h1>
      <p className="mt-1 text-sm text-crust-600">
        Tell us what you're picturing — we'll review and send back a quote.
      </p>
      <div className="mt-6">
        <CustomOrderForm />
      </div>
    </div>
  );
}

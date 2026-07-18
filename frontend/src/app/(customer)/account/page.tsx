"use client";

import { useAuth } from "@/hooks/useAuth";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { Button } from "@/components/ui/Button";
import { ROLE_LABELS } from "@/lib/constants";

export default function AccountPage() {
  const { user, isHydrating, signOut, requireAuth } = useAuth();
  requireAuth();

  if (isHydrating || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-sm px-4 py-16">
      <h1 className="font-display text-2xl font-semibold text-crust-900">
        {user.name}
      </h1>
      <p className="mt-1 text-sm text-crust-600">
        {user.email} · {ROLE_LABELS[user.role]}
      </p>
      <Button variant="secondary" className="mt-6" onClick={signOut}>
        Sign out
      </Button>
    </div>
  );
}

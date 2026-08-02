"use client";

import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/Button";

export default function StaffProfilePage() {
  const { user, signOut } = useAuth();

  return (
    <div className="mx-auto max-w-md px-4 py-6">
      <h1 className="font-display text-2xl font-semibold text-crust-900">
        Profile
      </h1>

      {user && (
        <div className="mt-4 rounded-xl border border-crust-100 bg-white p-4">
          <p className="text-sm font-medium text-crust-900">{user.name}</p>
          <p className="text-xs text-crust-500">{user.email}</p>
          <p className="text-xs text-crust-500">{user.phone}</p>
        </div>
      )}

      <Button variant="secondary" className="mt-6 w-fit" onClick={signOut}>
        Sign out
      </Button>
    </div>
  );
}

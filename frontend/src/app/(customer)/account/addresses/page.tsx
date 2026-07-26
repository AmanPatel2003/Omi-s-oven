"use client";

import { useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import {
  useGetAddressesQuery,
  useDeleteAddressMutation,
  useSetDefaultAddressMutation,
} from "@/store/api/addressesApi";
import { AddressForm } from "@/components/forms/AddressForm";
import { Button } from "@/components/ui/Button";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { cn } from "@/lib/utils";
import type { Address } from "@/types/api";

export default function AddressesPage() {
  const { requireAuth, isHydrating } = useAuth();
  requireAuth();

  const { data: addresses, isLoading } = useGetAddressesQuery();
  const [deleteAddress] = useDeleteAddressMutation();
  const [setDefaultAddress] = useSetDefaultAddressMutation();

  const [editing, setEditing] = useState<Address | null>(null);
  const [adding, setAdding] = useState(false);

  if (isHydrating || isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-xl px-4 py-8">
      <h1 className="font-display text-2xl font-semibold text-crust-900">
        Addresses
      </h1>

      <div className="mt-6 flex flex-col gap-4">
        {addresses?.map((addr) =>
          editing?.id === addr.id ? (
            <div
              key={addr.id}
              className="rounded-xl border border-crust-100 bg-white p-4"
            >
              <AddressForm existing={addr} onSaved={() => setEditing(null)} />
              <button
                type="button"
                onClick={() => setEditing(null)}
                className="mt-2 text-xs text-crust-500 underline"
              >
                Cancel
              </button>
            </div>
          ) : (
            <div
              key={addr.id}
              className={cn(
                "rounded-xl border bg-white p-4",
                addr.isDefault ? "border-crust-600" : "border-crust-100",
              )}
            >
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-crust-900">
                  {addr.addressType}
                  {addr.isDefault && (
                    <span className="ml-2 rounded-full bg-crust-100 px-2 py-0.5 text-xs text-crust-600">
                      Default
                    </span>
                  )}
                </p>
              </div>
              <p className="mt-1 text-sm text-crust-600">
                {addr.fullName} · {addr.phone}
                <br />
                {addr.addressLine1}
                {addr.addressLine2 ? `, ${addr.addressLine2}` : ""}, {addr.city}
                , {addr.state} {addr.postalCode}
              </p>
              <div className="mt-3 flex gap-3 text-xs">
                <button
                  type="button"
                  onClick={() => setEditing(addr)}
                  className="text-crust-600 underline"
                >
                  Edit
                </button>
                <button
                  type="button"
                  onClick={() => deleteAddress(addr.id)}
                  className="text-red-600 underline"
                >
                  Delete
                </button>
                {!addr.isDefault && (
                  <button
                    type="button"
                    onClick={() => setDefaultAddress(addr.id)}
                    className="text-crust-600 underline"
                  >
                    Set as default
                  </button>
                )}
              </div>
            </div>
          ),
        )}

        {adding ? (
          <div className="rounded-xl border border-crust-100 bg-white p-4">
            <AddressForm onSaved={() => setAdding(false)} />
            <button
              type="button"
              onClick={() => setAdding(false)}
              className="mt-2 text-xs text-crust-500 underline"
            >
              Cancel
            </button>
          </div>
        ) : (
          <Button variant="secondary" onClick={() => setAdding(true)}>
            + Add new address
          </Button>
        )}
      </div>
    </div>
  );
}

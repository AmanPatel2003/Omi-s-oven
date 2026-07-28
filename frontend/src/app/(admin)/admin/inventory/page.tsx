"use client";

import { useState } from "react";
import Link from "next/link";
import { useGetInventoryItemsQuery } from "@/store/api/adminInventoryApi";
import { AdjustInventoryModal } from "@/components/admin/AdjustInventoryModal";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { cn } from "@/lib/utils";
import type { InventoryItem, InventoryMovementType } from "@/types/api";

export default function AdminInventoryPage() {
  const { data: items, isLoading } = useGetInventoryItemsQuery();
  const [modal, setModal] = useState<{
    item: InventoryItem;
    type: InventoryMovementType;
  } | null>(null);

  if (isLoading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="font-display text-2xl font-semibold text-crust-900">
        Inventory
      </h1>

      <div className="mt-6 overflow-hidden rounded-xl border border-crust-100 bg-white">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-crust-100 bg-crust-50 text-left text-xs font-medium text-crust-500">
              <th className="px-3 py-2">Ingredient</th>
              <th className="px-3 py-2 text-right">Stock</th>
              <th className="px-3 py-2 text-right">Low stock at</th>
              <th className="px-3 py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {items?.map((item) => {
              const isLow = item.currentStock <= item.lowStockThreshold;
              return (
                <tr
                  key={item.id}
                  className={cn(
                    "border-b border-crust-50 last:border-0",
                    isLow && "bg-red-50",
                  )}
                >
                  <td className="px-3 py-2">{item.name}</td>
                  <td
                    className={cn(
                      "px-3 py-2 text-right",
                      isLow && "font-medium text-red-700",
                    )}
                  >
                    {item.currentStock} {item.unit}
                  </td>
                  <td className="px-3 py-2 text-right text-crust-500">
                    {item.lowStockThreshold} {item.unit}
                  </td>
                  <td className="px-3 py-2">
                    <div className="flex gap-3">
                      <button
                        type="button"
                        onClick={() => setModal({ item, type: "restock" })}
                        className="text-xs text-crust-600 underline"
                      >
                        Restock
                      </button>
                      <button
                        type="button"
                        onClick={() => setModal({ item, type: "adjustment" })}
                        className="text-xs text-crust-600 underline"
                      >
                        Adjust
                      </button>
                      <Link
                        href={`/admin/inventory/${item.id}/movements`}
                        className="text-xs text-crust-600 underline"
                      >
                        History
                      </Link>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {modal && (
        <AdjustInventoryModal
          item={modal.item}
          type={modal.type}
          onClose={() => setModal(null)}
        />
      )}
    </div>
  );
}

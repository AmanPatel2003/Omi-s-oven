"use client";

import { useState } from "react";
import { useAdjustInventoryMutation } from "@/store/api/adminInventoryApi";
import { Button } from "@/components/ui/Button";
import type { InventoryItem, InventoryMovementType } from "@/types/api";

export function AdjustInventoryModal({
  item,
  type,
  onClose,
}: {
  item: InventoryItem;
  type: InventoryMovementType;
  onClose: () => void;
}) {
  const [adjustInventory, { isLoading }] = useAdjustInventoryMutation();
  const [quantity, setQuantity] = useState(0);
  const [reason, setReason] = useState("");

  async function handleSubmit() {
    if (quantity === 0 || !reason.trim()) return;
    const signedQuantity = type === "restock" ? Math.abs(quantity) : quantity;
    await adjustInventory({
      id: item.id,
      quantity: signedQuantity,
      reason,
      type,
    });
    onClose();
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4">
      <div className="w-full max-w-sm rounded-xl bg-white p-5">
        <p className="font-medium text-crust-900">
          {type === "restock" ? "Restock" : "Adjust"} {item.name}
        </p>
        <p className="mt-1 text-xs text-crust-500">
          Current stock: {item.currentStock} {item.unit}
        </p>

        <div className="mt-4 flex flex-col gap-3">
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-crust-800">
              {type === "restock" ? "Quantity to add" : "Quantity (+/-)"}
            </label>
            <input
              type="number"
              value={quantity}
              onChange={(e) => setQuantity(Number(e.target.value))}
              className="rounded-lg border border-crust-200 px-3 py-2 text-sm"
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-crust-800">Reason</label>
            <input
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="e.g. Supplier delivery, spoilage, recount…"
              className="rounded-lg border border-crust-200 px-3 py-2 text-sm"
            />
          </div>
        </div>

        <div className="mt-5 flex justify-end gap-3">
          <Button variant="secondary" className="w-auto px-4" onClick={onClose}>
            Cancel
          </Button>
          <Button
            className="w-auto px-4"
            isLoading={isLoading}
            disabled={quantity === 0 || !reason.trim()}
            onClick={handleSubmit}
          >
            Save
          </Button>
        </div>
      </div>
    </div>
  );
}

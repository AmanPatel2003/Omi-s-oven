"use client";

import { useState } from "react";
import { useUpdateProductStockMutation } from "@/store/api/adminProductsApi";
import { Button } from "@/components/ui/Button";
import type { AdminProduct } from "@/types/api";

export function StockAdjustmentPanel({ product }: { product: AdminProduct }) {
  const [updateStock, { isLoading }] = useUpdateProductStockMutation();
  const [values, setValues] = useState<Record<string, number>>(
    product.variants.length > 0
      ? Object.fromEntries(
          product.variants.map((v) => [v.id ?? v.name, v.stock]),
        )
      : { base: product.stock },
  );
  const [reason, setReason] = useState("");
  const [success, setSuccess] = useState(false);

  async function saveOne(variantId: string | undefined, stock: number) {
    setSuccess(false);
    await updateStock({
      id: product.id,
      variantId,
      stock,
      reason: reason || undefined,
    });
    setSuccess(true);
  }

  return (
    <div className="rounded-xl border border-crust-100 bg-white p-4">
      <p className="text-sm font-semibold text-crust-800">Adjust stock</p>
      <p className="mt-1 text-xs text-crust-500">
        Separate from the main product form — this calls its own endpoint
        immediately per row.
      </p>

      <div className="mt-3 flex flex-col gap-2">
        {product.variants.length > 0 ? (
          product.variants.map((v) => (
            <div key={v.id ?? v.name} className="flex items-center gap-2">
              <span className="w-24 text-sm text-crust-700">{v.name}</span>
              <input
                type="number"
                value={values[v.id ?? v.name]}
                onChange={(e) =>
                  setValues((prev) => ({
                    ...prev,
                    [v.id ?? v.name]: Number(e.target.value),
                  }))
                }
                className="w-24 rounded-lg border border-crust-200 px-2 py-1.5 text-sm"
              />
              <Button
                variant="secondary"
                className="w-auto px-3 py-1.5 text-xs"
                isLoading={isLoading}
                onClick={() => saveOne(v.id, values[v.id ?? v.name])}
              >
                Save
              </Button>
            </div>
          ))
        ) : (
          <div className="flex items-center gap-2">
            <span className="w-24 text-sm text-crust-700">Stock</span>
            <input
              type="number"
              value={values.base}
              onChange={(e) =>
                setValues((prev) => ({ ...prev, base: Number(e.target.value) }))
              }
              className="w-24 rounded-lg border border-crust-200 px-2 py-1.5 text-sm"
            />
            <Button
              variant="secondary"
              className="w-auto px-3 py-1.5 text-xs"
              isLoading={isLoading}
              onClick={() => saveOne(undefined, values.base)}
            >
              Save
            </Button>
          </div>
        )}

        <input
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="Reason (optional)"
          className="mt-2 rounded-lg border border-crust-200 px-2 py-1.5 text-sm"
        />
        {success && <p className="text-xs text-green-700">Stock updated.</p>}
      </div>
    </div>
  );
}

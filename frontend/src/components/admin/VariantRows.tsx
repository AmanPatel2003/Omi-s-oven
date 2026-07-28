"use client";

import type { AdminProductVariant } from "@/types/api";

export function VariantRows({
  variants,
  onChange,
}: {
  variants: AdminProductVariant[];
  onChange: (variants: AdminProductVariant[]) => void;
}) {
  function updateRow(index: number, patch: Partial<AdminProductVariant>) {
    onChange(variants.map((v, i) => (i === index ? { ...v, ...patch } : v)));
  }

  function addRow() {
    onChange([...variants, { name: "", price: 0, stock: 0 }]);
  }

  function removeRow(index: number) {
    onChange(variants.filter((_, i) => i !== index));
  }

  return (
    <div className="flex flex-col gap-2">
      {variants.map((variant, i) => (
        <div
          key={variant.id ?? `new-${i}`}
          className="grid grid-cols-[1fr_100px_100px_auto] gap-2"
        >
          <input
            value={variant.name}
            onChange={(e) => updateRow(i, { name: e.target.value })}
            placeholder="e.g. 500g"
            className="rounded-lg border border-crust-200 px-2 py-1.5 text-sm"
          />
          <input
            type="number"
            value={variant.price}
            onChange={(e) => updateRow(i, { price: Number(e.target.value) })}
            placeholder="Price"
            className="rounded-lg border border-crust-200 px-2 py-1.5 text-sm"
          />
          <input
            type="number"
            value={variant.stock}
            onChange={(e) => updateRow(i, { stock: Number(e.target.value) })}
            placeholder="Stock"
            className="rounded-lg border border-crust-200 px-2 py-1.5 text-sm"
          />
          <button
            type="button"
            onClick={() => removeRow(i)}
            aria-label="Remove variant"
            className="text-crust-400"
          >
            ✕
          </button>
        </div>
      ))}
      <button
        type="button"
        onClick={addRow}
        className="w-fit text-xs text-crust-600 underline"
      >
        + Add variant
      </button>
    </div>
  );
}

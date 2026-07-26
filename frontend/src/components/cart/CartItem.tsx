"use client";

import Image from "next/image";
import {
  useUpdateCartItemMutation,
  useRemoveFromCartMutation,
} from "@/store/api/cartApi";
import { formatCurrency } from "@/lib/utils";
import type { CartItem as CartItemType } from "@/types/api";

export function CartItem({ item }: { item: CartItemType }) {
  const [updateCartItem] = useUpdateCartItemMutation();
  const [removeFromCart] = useRemoveFromCartMutation();

  function changeQuantity(delta: number) {
    const next = item.quantity + delta;
    if (next <= 0) {
      removeFromCart(item.productId);
      return;
    }
    updateCartItem({ itemId: item.id, quantity: next });
  }

  const overStock = item.inStock && item.quantity > item.availableStock;

  return (
    <div className="flex gap-3 border-b border-crust-100 py-3">
      <div className="relative h-16 w-16 flex-shrink-0 overflow-hidden rounded-lg bg-crust-50">
        {item.image && (
          <Image
            src={item.image}
            alt={item.name}
            fill
            className="object-cover"
          />
        )}
      </div>

      <div className="flex flex-1 flex-col gap-1">
        <p className="text-sm font-medium text-crust-900">{item.name}</p>
        <p className="text-sm text-crust-600">
          {formatCurrency(item.unitPrice)}
        </p>

        {!item.inStock && (
          <p className="text-xs text-red-600">
            This item is currently out of stock.
          </p>
        )}
        {item.inStock && overStock && (
          <p className="text-xs text-amber-600">
            Only {item.availableStock} left — reduce quantity to check out.
          </p>
        )}

        <div className="mt-1 flex items-center gap-2">
          <button
            type="button"
            onClick={() => changeQuantity(-1)}
            aria-label="Decrease quantity"
            className="h-7 w-7 rounded-full border border-crust-200 text-sm"
          >
            −
          </button>
          <span className="w-6 text-center text-sm">{item.quantity}</span>
          <button
            type="button"
            onClick={() => changeQuantity(1)}
            aria-label="Increase quantity"
            className="h-7 w-7 rounded-full border border-crust-200 text-sm"
            disabled={item.inStock && item.quantity >= item.availableStock}
          >
            +
          </button>
        </div>
      </div>

      <div className="flex flex-col items-end justify-between">
        <p className="text-sm font-semibold text-crust-900">
          {formatCurrency(item.lineTotal)}
        </p>
        <button
          type="button"
          onClick={() => removeFromCart(item.productId)}
          className="text-xs text-crust-400 underline"
        >
          Remove
        </button>
      </div>
    </div>
  );
}

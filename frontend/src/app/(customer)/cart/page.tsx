"use client";

import { useState } from "react";
import {
  useGetCartQuery,
  useApplyCouponMutation,
  useRemoveCouponMutation,
} from "@/store/api/cartApi";
import { useValidateCouponMutation } from "@/store/api/couponsApi";
import { CartItem } from "@/components/cart/CartItem";
import { CartSummary } from "@/components/cart/CartSummary";
import { Button } from "@/components/ui/Button";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { formatCurrency } from "@/lib/utils";
import type { ValidateCouponResponse } from "@/types/api";

export default function CartPage() {
  const { data: cart, isLoading } = useGetCartQuery();
  const [validateCoupon, { isLoading: isValidating }] =
    useValidateCouponMutation();
  const [applyCoupon, { isLoading: isApplying }] = useApplyCouponMutation();
  const [removeCoupon] = useRemoveCouponMutation();

  const [couponInput, setCouponInput] = useState("");
  const [preview, setPreview] = useState<ValidateCouponResponse | null>(null);

  const subtotal =
    cart?.items.reduce((sum, item) => sum + item.lineTotal, 0) ?? 0;

  async function handleValidateOnBlur() {
    if (!couponInput.trim()) {
      setPreview(null);
      return;
    }
    try {
      const result = await validateCoupon({
        code: couponInput.trim(),
        cartTotal: subtotal,
      }).unwrap();
      setPreview(result);
    } catch {
      setPreview({
        valid: false,
        coupon: null,
        estimatedDiscount: 0,
        message: "Couldn't check that code.",
      });
    }
  }

  async function handleApply() {
    if (!couponInput.trim()) return;
    await applyCoupon({ code: couponInput.trim() });
    setPreview(null);
  }

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  if (!cart || cart.items.length === 0) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16 text-center">
        <p className="text-crust-600">Your cart is empty.</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <h1 className="font-display text-2xl font-semibold text-crust-900">
        Your Cart
      </h1>

      <div className="mt-6 grid gap-8 md:grid-cols-[1fr_320px]">
        <div>
          {cart.items.map((item) => (
            <CartItem key={item.id} item={item} />
          ))}
        </div>

        <div className="flex flex-col gap-4">
          <div className="rounded-xl border border-crust-100 bg-white p-4">
            {cart.couponCode ? (
              <div className="flex items-center justify-between text-sm">
                <span className="text-crust-700">
                  Coupon <strong>{cart.couponCode}</strong> applied
                </span>
                <button
                  type="button"
                  onClick={() => removeCoupon()}
                  className="text-crust-400 underline"
                >
                  Remove
                </button>
              </div>
            ) : (
              <div className="flex flex-col gap-2">
                <label
                  className="text-sm font-medium text-crust-800"
                  htmlFor="coupon"
                >
                  Coupon code
                </label>
                <input
                  id="coupon"
                  value={couponInput}
                  onChange={(e) => setCouponInput(e.target.value)}
                  onBlur={handleValidateOnBlur}
                  placeholder="Enter code"
                  className="rounded-xl border border-crust-200 px-3 py-2 text-sm"
                />
                {isValidating && (
                  <p className="text-xs text-crust-500">Checking…</p>
                )}
                {preview && (
                  <p
                    className={`text-xs ${preview.valid ? "text-green-700" : "text-red-600"}`}
                  >
                    {preview.valid
                      ? `Saves ${formatCurrency(preview.estimatedDiscount)} — ${preview.message}`
                      : preview.message}
                  </p>
                )}
                <Button
                  variant="secondary"
                  onClick={handleApply}
                  isLoading={isApplying}
                  disabled={!preview?.valid}
                >
                  Apply
                </Button>
              </div>
            )}
          </div>

          <CartSummary />

          <Button>Proceed to Checkout</Button>
        </div>
      </div>
    </div>
  );
}

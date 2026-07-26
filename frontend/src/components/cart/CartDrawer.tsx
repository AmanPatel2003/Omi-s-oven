"use client";

import Link from "next/link";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { closeCart } from "@/store/slices/uiSlice";
import { useGetCartQuery } from "@/store/api/cartApi";
import { CartItem } from "@/components/cart/CartItem";
import { Button } from "@/components/ui/Button";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { formatCurrency, cn } from "@/lib/utils";

export function CartDrawer() {
  const isOpen = useAppSelector((state) => state.ui.isCartOpen);
  const dispatch = useAppDispatch();
  const { data: cart, isLoading } = useGetCartQuery(undefined, {
    skip: !isOpen,
  });

  const subtotal =
    cart?.items.reduce((sum, item) => sum + item.lineTotal, 0) ?? 0;

  return (
    <>
      <div
        className={cn(
          "fixed inset-0 z-40 bg-black/30 transition-opacity",
          isOpen ? "opacity-100" : "pointer-events-none opacity-0",
        )}
        onClick={() => dispatch(closeCart())}
        aria-hidden
      />

      <div
        role="dialog"
        aria-label="Shopping cart"
        aria-hidden={!isOpen}
        className={cn(
          "fixed right-0 top-0 z-50 flex h-full w-full max-w-sm flex-col bg-white shadow-xl transition-transform duration-300",
          isOpen ? "translate-x-0" : "translate-x-full",
        )}
      >
        <div className="flex items-center justify-between border-b border-crust-100 p-4">
          <h2 className="font-display text-lg font-semibold text-crust-900">
            Your Cart
          </h2>
          <button
            type="button"
            onClick={() => dispatch(closeCart())}
            aria-label="Close cart"
            className="text-crust-500"
          >
            ✕
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          {isLoading ? (
            <div className="flex justify-center py-8">
              <LoadingSpinner />
            </div>
          ) : !cart || cart.items.length === 0 ? (
            <p className="py-8 text-center text-sm text-crust-500">
              Your cart is empty.
            </p>
          ) : (
            cart.items.map((item) => <CartItem key={item.id} item={item} />)
          )}
        </div>

        {cart && cart.items.length > 0 && (
          <div className="border-t border-crust-100 p-4">
            <div className="mb-3 flex justify-between text-sm font-medium text-crust-900">
              <span>Subtotal</span>
              <span>{formatCurrency(subtotal)}</span>
            </div>
            <Link href="/checkout" onClick={() => dispatch(closeCart())}>
              <Button>Checkout</Button>
            </Link>
            <Link
              href="/cart"
              onClick={() => dispatch(closeCart())}
              className="mt-2 block text-center text-sm text-crust-600 underline"
            >
              View full cart
            </Link>
          </div>
        )}
      </div>
    </>
  );
}

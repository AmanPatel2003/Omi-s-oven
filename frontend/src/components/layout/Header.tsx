"use client";

import Link from "next/link";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { toggleCart } from "@/store/slices/uiSlice";
import { useGetCartQuery } from "@/store/api/cartApi";
import { useAuth } from "@/hooks/useAuth";
import { NotificationBell } from "@/components/layout/NotificationBell";

export function Header() {
  const dispatch = useAppDispatch();
  const { isAuthenticated } = useAuth();
  const { data: cart } = useGetCartQuery(undefined, { skip: !isAuthenticated });
  const itemCount = cart?.items.reduce((sum, i) => sum + i.quantity, 0) ?? 0;

  return (
    <header className="sticky top-0 z-30 border-b border-crust-100 bg-crust-50/95 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Link
          href="/"
          className="font-display text-lg font-semibold text-crust-900"
        >
          The Bakery
        </Link>

        <nav className="flex items-center gap-5 text-sm text-crust-700">
          <Link href="/products">Products</Link>
          {isAuthenticated ? (
            <Link href="/account">Account</Link>
          ) : (
            <Link href="/auth/login">Sign in</Link>
          )}
          {isAuthenticated && <NotificationBell />}
          <button
            type="button"
            onClick={() => dispatch(toggleCart())}
            aria-label="Open cart"
            className="relative"
          >
            🛒
            {itemCount > 0 && (
              <span className="absolute -right-2 -top-2 flex h-4 w-4 items-center justify-center rounded-full bg-crust-600 text-[10px] text-white">
                {itemCount}
              </span>
            )}
          </button>
        </nav>
      </div>
    </header>
  );
}

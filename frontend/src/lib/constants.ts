import type { UserRole } from "@/types/api";

/** Name of the httpOnly cookie holding the refresh token — set/read only by
 * Route Handlers (src/app/api/auth/*) and checked (presence-only) by
 * middleware.ts. Never read this from client components. */
export const REFRESH_COOKIE_NAME = "bakery_refresh_token";

export const ROLE_LABELS: Record<UserRole, string> = {
  customer: "Customer",
  staff: "Delivery Staff",
  admin: "Admin",
};

export const ORDER_STATUSES = [
  "pending",
  "confirmed",
  "preparing",
  "out_for_delivery",
  "delivered",
  "cancelled",
] as const;
export type OrderStatus = (typeof ORDER_STATUSES)[number];

/** Route-group prefixes gated by middleware.ts — see Auth Module step 6. */
export const PROTECTED_PREFIXES = ["/account", "/admin", "/staff"] as const;

export const AUTH_PAGES = ["/auth/login", "/auth/register"] as const;

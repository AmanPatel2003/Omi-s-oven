import type { UserRole } from "@/types/api";

/** Name of the httpOnly cookie holding the refresh token — set/read only by
 * Route Handlers (src/app/api/auth/*) and checked (presence-only) by
 * middleware.ts. Never read this from client components. */
export const REFRESH_COOKIE_NAME = "bakery_refresh_token";

/** Name of the plain (non-httpOnly) cookie holding just the user's role
 * string, set alongside REFRESH_COOKIE_NAME. Exists only so middleware.ts
 * can do the UX-level admin/staff redirect without a network round trip —
 * see the comment in app/api/auth/_shared.ts for why this isn't a security
 * boundary. */
export const ROLE_COOKIE_NAME = "bakery_role";

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

export const SORT_OPTIONS: {
  value: import("@/types/api").ProductSort;
  label: string;
}[] = [
  { value: "bestselling", label: "Bestselling" },
  { value: "newest", label: "Newest" },
  { value: "price_asc", label: "Price: Low to High" },
  { value: "price_desc", label: "Price: High to Low" },
  { value: "rating", label: "Rating" },
];

// Deliberately its own list, not reused from ORDER_STATUSES — the spec is
// explicit that these need a distinct palette so users don't confuse a
// custom-cake quote workflow with a regular order's delivery status, even
// though a couple of the words overlap ("pending", "cancelled").
export const CUSTOM_ORDER_STATUSES = [
  "pending",
  "reviewing",
  "quoted",
  "confirmed",
  "in_progress",
  "completed",
  "rejected",
  "cancelled",
] as const;
export type CustomOrderStatus = (typeof CUSTOM_ORDER_STATUSES)[number];

/** Mirrors the backend's MIN_LEAD_TIME_HOURS for client-side validation on
 * the custom-order "needed by" date picker — keep these in sync. */
export const MIN_LEAD_TIME_HOURS = 48;

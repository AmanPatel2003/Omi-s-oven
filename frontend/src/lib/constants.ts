import type { UserRole } from "@/types/api";

/** Name of the httpOnly cookie holding the refresh token — set/read only by
 * Route Handlers (src/app/api/auth/*) and checked (presence-only) by
 * middleware.ts. Never read this from client components. */
export const REFRESH_COOKIE_NAME = "refresh_token";

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
  super_admin: "Super Admin",
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

/**
 * Mirrors the backend's VALID_TRANSITIONS map, per the spec's explicit
 * instruction: <StatusTransitionButton> must only render buttons for legal
 * next-states, derived from this constant, not trial-and-error.
 *
 * IMPORTANT: this is a guess at a reasonable linear bakery order flow
 * (pending → confirmed → preparing → out_for_delivery → delivered, with
 * cancellation possible up through preparing but not after dispatch). The
 * actual backend map was never provided anywhere in the build spec — there
 * is no source of truth to copy this from. Treat every transition here as
 * unconfirmed until checked against the real backend; getting this wrong
 * means either hiding a legal action or showing one the backend rejects.
 */
export const VALID_ORDER_TRANSITIONS: Record<OrderStatus, OrderStatus[]> = {
  pending: ["confirmed", "cancelled"],
  confirmed: ["preparing", "cancelled"],
  preparing: ["out_for_delivery", "cancelled"],
  out_for_delivery: ["delivered"],
  delivered: [],
  cancelled: [],
};

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

export const MIN_LEAD_TIME_HOURS = 48;

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

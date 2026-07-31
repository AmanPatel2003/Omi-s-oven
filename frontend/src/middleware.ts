import { NextResponse, type NextRequest } from "next/server";
import {
  PROTECTED_PREFIXES,
  REFRESH_COOKIE_NAME,
  ROLE_COOKIE_NAME,
} from "@/lib/constants";
import type { UserRole } from "@/types/api";

const ROLE_GATED_PREFIXES: Partial<Record<string, UserRole[]>> = {
  "/admin": ["admin", "super_admin"],
  "/staff": ["staff"],
};

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  const isProtected = PROTECTED_PREFIXES.some((prefix) =>
    pathname.startsWith(prefix),
  );
  if (!isProtected) {
    return NextResponse.next();
  }

  const hasSession = request.cookies.has(REFRESH_COOKIE_NAME);
  if (!hasSession) {
    const loginUrl = new URL("/auth/login", request.url);
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  const gatedPrefix = Object.keys(ROLE_GATED_PREFIXES).find((prefix) =>
    pathname.startsWith(prefix),
  );
  if (gatedPrefix) {
    const allowedRoles = ROLE_GATED_PREFIXES[gatedPrefix]!;
    const role = request.cookies.get(ROLE_COOKIE_NAME)?.value as
      | UserRole
      | undefined;
    if (!role || !allowedRoles.includes(role)) {
      return NextResponse.redirect(new URL("/", request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/account/:path*", "/admin/:path*", "/staff/:path*"],
};

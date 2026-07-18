import { NextResponse, type NextRequest } from "next/server";
import { PROTECTED_PREFIXES, REFRESH_COOKIE_NAME } from "@/lib/constants";

/**
 * Redirects to /auth/login when a protected route is hit with no refresh
 * cookie present at all. This only checks presence, not validity — that's
 * inherently the backend's job since middleware can't verify a JWT against
 * the backend's secret without an extra round trip on every request. Real
 * authorization (role checks, expired/forged tokens) happens server-side
 * via the JWT `role` claim when the actual API call is made; this
 * middleware exists purely to avoid rendering a protected page's shell for
 * a visitor who is obviously logged out.
 */
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  const isProtected = PROTECTED_PREFIXES.some((prefix) =>
    pathname.startsWith(prefix)
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

  return NextResponse.next();
}

export const config = {
  matcher: ["/account/:path*", "/admin/:path*", "/staff/:path*"],
};

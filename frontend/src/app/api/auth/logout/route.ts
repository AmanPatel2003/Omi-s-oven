import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { REFRESH_COOKIE, BACKEND_URL } from "@/app/api/auth/_shared";

/**
 * POST /api/auth/logout
 *
 * Tells the backend to revoke the refresh token (so it can't be replayed
 * even if it leaked) and clears the httpOnly cookie. Called from
 * authSlice's `logout` reducer flow — see hooks/useAuth.ts.
 */
export async function POST() {
  const refreshToken = cookies().get(REFRESH_COOKIE)?.value;

  if (refreshToken) {
    await fetch(`${BACKEND_URL}/auth/logout`, {
      method: "POST",
      headers: { Cookie: `refresh_token=${refreshToken}` },
    }).catch(() => {
      // Best-effort — the cookie gets cleared locally regardless, so the
      // user is logged out client-side even if the backend call fails.
    });
  }

  cookies().delete(REFRESH_COOKIE);
  return NextResponse.json({ success: true, data: null, message: "Logged out" });
}

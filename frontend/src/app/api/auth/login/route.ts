import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";
import {
  REFRESH_COOKIE,
  REFRESH_COOKIE_OPTIONS,
  BACKEND_URL,
} from "@/app/api/auth/_shared";
import { ROLE_COOKIE_NAME } from "@/lib/constants";

/**
 * POST /api/auth/login
 *
 * Proxies to the backend's /auth/login. The backend is expected to return
 * the refresh token as a field in the JSON body (not a cookie of its own —
 * it doesn't share a domain with the browser). This handler pulls the
 * refresh token out of that response, sets it as an httpOnly cookie scoped
 * to this Next.js origin, and strips it before forwarding the rest of the
 * envelope to the browser. Browser JS therefore never sees the refresh
 * token in any form.
 */
export async function POST(req: NextRequest) {
  const body = await req.json();

  const backendRes = await fetch(`${BACKEND_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  const envelope = await backendRes.json();

  if (!backendRes.ok) {
    return NextResponse.json(envelope, { status: backendRes.status });
  }

  const { refresh_token, ...tokenData } = envelope.data;
  cookies().set(REFRESH_COOKIE, refresh_token, REFRESH_COOKIE_OPTIONS);
  cookies().set(ROLE_COOKIE_NAME, tokenData.user.role, REFRESH_COOKIE_OPTIONS);

  return NextResponse.json(
    { ...envelope, data: tokenData },
    { status: backendRes.status },
  );
}

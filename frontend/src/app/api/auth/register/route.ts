import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";
import {
  REFRESH_COOKIE,
  REFRESH_COOKIE_OPTIONS,
  BACKEND_URL,
} from "@/app/api/auth/_shared";

/**
 * POST /api/auth/register
 *
 * Same proxy-and-extract-refresh-token pattern as /api/auth/login (see that
 * handler's comment). Kept as a separate route rather than a shared branch
 * so the two can diverge independently (e.g. if registration later needs a
 * welcome-email side effect) without an if/else on request type.
 */
export async function POST(req: NextRequest) {
  const body = await req.json();

  const backendRes = await fetch(`${BACKEND_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  const envelope = await backendRes.json();

  if (!backendRes.ok) {
    return NextResponse.json(envelope, { status: backendRes.status });
  }

  const { refreshToken, ...tokenData } = envelope.data;
  cookies().set(REFRESH_COOKIE, refreshToken, REFRESH_COOKIE_OPTIONS);

  return NextResponse.json(
    { ...envelope, data: tokenData },
    { status: backendRes.status }
  );
}

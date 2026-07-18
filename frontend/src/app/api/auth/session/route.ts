import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { exchangeRefreshToken } from "@/app/api/auth/_shared";

/**
 * GET /api/auth/session
 *
 * Called once on app load (see app/providers.tsx) to hydrate Redux from the
 * httpOnly refresh cookie without ever exposing that cookie to browser JS.
 * A 401 just means the visitor isn't logged in — not an error to surface.
 */
export async function GET() {
  const result = await exchangeRefreshToken(cookies());
  if (!result) {
    return NextResponse.json({ message: "No session" }, { status: 401 });
  }
  return NextResponse.json(result.envelope, { status: result.status });
}

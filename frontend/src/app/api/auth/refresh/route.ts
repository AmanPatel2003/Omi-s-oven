import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { exchangeRefreshToken } from "@/app/api/auth/_shared";

/**
 * POST /api/auth/refresh
 *
 * Same-origin endpoint the browser calls when it needs a new access token
 * (the store's baseQueryWithReauth 401 path). Being same-origin means the
 * httpOnly cookie is sent automatically without any client JS reading it.
 */
export async function POST() {
  const result = await exchangeRefreshToken(cookies());
  if (!result) {
    return NextResponse.json({ message: "Session expired" }, { status: 401 });
  }
  return NextResponse.json(result.envelope, { status: result.status });
}

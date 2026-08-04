import { REFRESH_COOKIE_NAME } from "@/lib/constants";

export const REFRESH_COOKIE = REFRESH_COOKIE_NAME;
// export const BACKEND_URL = process.env.NEXT_PUBLIC_API_BASE_URL;
export const BACKEND_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

export const REFRESH_COOKIE_OPTIONS = {
  httpOnly: true,
  secure: process.env.NODE_ENV === "production",
  sameSite: "lax" as const,
  path: "/",
  // Matches the backend's refresh token lifetime. Kept in one place so it's
  // obvious this needs to change if the backend's expiry changes.
  maxAge: 60 * 60 * 24 * 30, // 30 days
};

/**
 * Exchanges the cookie's refresh token for a fresh access token against the
 * backend, re-setting the cookie if the backend rotates it. Shared by
 * /api/auth/refresh (called by the client's 401 retry) and
 * /api/auth/session (called once on app load) so the two never drift.
 * Returns null if there's no cookie or the backend rejects it.
 */
export async function exchangeRefreshToken(
  cookieStore: ReturnType<typeof import("next/headers").cookies>,
): Promise<{ envelope: unknown; status: number } | null> {
  const refreshToken = cookieStore.get(REFRESH_COOKIE)?.value;
  if (!refreshToken) return null;

  const backendRes = await fetch(`${BACKEND_URL}/auth/refresh`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      refresh_token: refreshToken,
    }),
  });

  if (!backendRes.ok) {
    cookieStore.delete(REFRESH_COOKIE);
    return null;
  }

  const envelope = await backendRes.json();
  if (envelope.data?.refresh_token) {
    const { refresh_token: rotated, ...tokenData } = envelope.data;
    cookieStore.set(REFRESH_COOKIE, rotated, REFRESH_COOKIE_OPTIONS);
    envelope.data = tokenData;
  }
  return { envelope, status: backendRes.status };
}

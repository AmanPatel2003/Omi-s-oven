"use client";

import { useEffect, useRef, useState } from "react";
import { Provider } from "react-redux";
import { makeStore, type AppStore } from "@/store/store";
import { setCredentials, setHydrated } from "@/store/slices/authSlice";
import type { ApiEnvelope, RefreshResponse } from "@/types/api";

/**
 * Calls the Route Handler at /api/auth/session, which reads the httpOnly
 * refresh cookie server-side, exchanges it with the backend's
 * /auth/refresh, and returns a fresh access token + user. This is how
 * Redux state gets hydrated on a hard reload without ever exposing the
 * refresh token to browser JS. A 401/no-cookie response just means the
 * visitor isn't logged in — that's not an error, so it's handled quietly.
 */
async function hydrateSession(store: AppStore) {
  try {
    const res = await fetch("/api/auth/session", { method: "GET" });
    if (res.ok) {
      const envelope = (await res.json()) as ApiEnvelope<RefreshResponse>;
      store.dispatch(
        setCredentials({
          user: envelope.data.user,
          access_token: envelope.data.access_token,
        }),
      );
    }
  } catch {
    // No session, or the backend is unreachable — proceed logged-out.
  } finally {
    store.dispatch(setHydrated());
  }
}

export function Providers({ children }: { children: React.ReactNode }) {
  const storeRef = useRef<AppStore>();
  if (!storeRef.current) {
    storeRef.current = makeStore();
  }
  const [ready] = useState(true);

  useEffect(() => {
    hydrateSession(storeRef.current!);
    // Runs once on mount only — the store instance is stable for the life
    // of the tab.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (!ready) return null;

  return <Provider store={storeRef.current}>{children}</Provider>;
}

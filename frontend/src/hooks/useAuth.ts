"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { useLogoutMutation } from "@/store/api/authApi";
import { logout as logoutAction } from "@/store/slices/authSlice";
import type { UserRole } from "@/types/api";

export function useAuth() {
  const dispatch = useAppDispatch();
  const router = useRouter();
  const { user, isAuthenticated, isHydrating } = useAppSelector(
    (state) => state.auth
  );
  const [logoutMutation] = useLogoutMutation();

  const role: UserRole | null = user?.role ?? null;

  async function signOut() {
    // Clear local state immediately for a snappy UI, then tell the server
    // to revoke the refresh token and drop the httpOnly cookie. Order
    // matters less here than making sure both happen even if one fails.
    dispatch(logoutAction());
    await logoutMutation();
    router.push("/auth/login");
  }

  /**
   * Client-component route guard: redirects to /auth/login if the session
   * has finished hydrating and the visitor still isn't authenticated.
   * Complements middleware.ts (which only checks cookie presence) — this
   * catches the case where hydration determined the cookie was stale.
   */
  function requireAuth(allowedRoles?: UserRole[]) {
    useEffect(() => {
      if (isHydrating) return;
      if (!isAuthenticated) {
        router.replace("/auth/login");
        return;
      }
      if (allowedRoles && role && !allowedRoles.includes(role)) {
        router.replace("/");
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isHydrating, isAuthenticated, role]);
  }

  return { user, role, isAuthenticated, isHydrating, signOut, requireAuth };
}

import {
  createApi,
  fetchBaseQuery,
  type BaseQueryFn,
  type FetchArgs,
  type FetchBaseQueryError,
} from "@reduxjs/toolkit/query/react";
import type { RootState } from "@/store/store";
import { logout, setCredentials } from "@/store/slices/authSlice";
import type { ApiEnvelope, RefreshResponse } from "@/types/api";

// Talks to the real backend for everything except the refresh dance. Sends
// the access token as a Bearer header — never a cookie — since the backend
// and frontend are on different origins in general.
// const rawBaseQuery = fetchBaseQuery({
//   baseUrl: process.env.NEXT_PUBLIC_API_URL,
//   prepareHeaders: (headers, { getState }) => {
//     const token = (getState() as RootState).auth.access_token;
//     if (token) {
//       headers.set("Authorization", `Bearer ${token}`);
//     }
//     return headers;
//   },
// });

const rawBaseQuery = fetchBaseQuery({
  // baseUrl: process.env.NEXT_PUBLIC_API_URL,
  baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL,
  // prepareHeaders: (headers, { getState }) => {
  //   const state = getState() as RootState;

  //   const token = state.auth?.access_token;

  //   if (token) {
  //     headers.set("Authorization", `Bearer ${token}`);
  //   }

  //   return headers;
  // },
  prepareHeaders: (headers, { getState }) => {
    const token = (getState() as RootState).auth.access_token;

    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }

    return headers;
  },
});

// Talks to this Next.js app's own origin. Used only for /api/auth/refresh,
// which is the one call that needs the httpOnly refresh cookie — a cookie
// that only ever gets sent automatically because this request stays
// same-origin. `credentials: "include"` here is what makes that happen from
// the browser.
const localBaseQuery = fetchBaseQuery({
  baseUrl: "",
  credentials: "include",
});

/**
 * Wraps the raw query so that a 401 triggers exactly one silent refresh
 * attempt against the local /api/auth/refresh Route Handler (which owns the
 * httpOnly cookie and proxies the real backend — see
 * app/api/auth/refresh/route.ts), then retries the original request once
 * with the new access token. If the refresh itself fails, the user is
 * logged out client-side — redirecting to /auth/login is left to the
 * component/route via `isAuthenticated`, not done here, so this stays
 * reusable outside React.
 *
 * This is the `baseQueryWithReauth` pattern referenced in the Auth Module
 * spec (step 3). A module-level mutex prevents two concurrent 401s from
 * both firing a refresh request.
 */
let refreshPromise: Promise<boolean> | null = null;

const baseQueryWithReauth: BaseQueryFn<
  string | FetchArgs,
  unknown,
  FetchBaseQueryError
> = async (args, api, extraOptions) => {
  let result = await rawBaseQuery(args, api, extraOptions);

  if (result.error && result.error.status === 401) {
    if (!refreshPromise) {
      refreshPromise = (async () => {
        const refreshResult = await localBaseQuery(
          { url: "/api/auth/refresh", method: "POST" },
          api,
          extraOptions,
        );
        if (refreshResult.data) {
          const envelope = refreshResult.data as ApiEnvelope<RefreshResponse>;
          api.dispatch(
            setCredentials({
              user: envelope.data.user,
              access_token: envelope.data.access_token,
            }),
          );
          return true;
        }
        api.dispatch(logout());
        return false;
      })().finally(() => {
        refreshPromise = null;
      });
    }

    const refreshed = await refreshPromise;
    if (refreshed) {
      result = await rawBaseQuery(args, api, extraOptions);
    }
  }

  return result;
};

export const baseApi = createApi({
  reducerPath: "api",
  baseQuery: baseQueryWithReauth,
  tagTypes: [
    "User",
    "Product",
    "Category",
    "Cart",
    "Order",
    "CustomOrder",
    "Delivery",
    "Reward",
    "Coupon",
    "Notification",
    "Reviews",
    "Address",
  ],
  endpoints: () => ({}),
});

import { fetchBaseQuery } from "@reduxjs/toolkit/query/react";
import { baseApi } from "@/store/api/baseApi";
import type {
  ApiEnvelope,
  ChangePasswordRequest,
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  RegisterResponse,
  User,
} from "@/types/api";

// Login/register/logout are proxied through this app's own Route Handlers
// (src/app/api/auth/*) rather than hitting the backend directly, because
// those handlers are what read/write the httpOnly refresh-token cookie —
// see the comment in store/api/baseApi.ts. This query has no baseUrl, so
// "/api/auth/login" resolves against the current origin, not the backend.
const localAuthQuery = fetchBaseQuery({ baseUrl: "" });

export const authApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    login: builder.mutation<LoginResponse, LoginRequest>({
      queryFn: async (body, api, extraOptions) => {
        const result = await localAuthQuery(
          { url: "/api/auth/login", method: "POST", body },
          api,
          extraOptions
        );
        if (result.error) return { error: result.error };
        return { data: (result.data as ApiEnvelope<LoginResponse>).data };
      },
      invalidatesTags: ["User"],
    }),

    register: builder.mutation<RegisterResponse, RegisterRequest>({
      queryFn: async (body, api, extraOptions) => {
        const result = await localAuthQuery(
          { url: "/api/auth/register", method: "POST", body },
          api,
          extraOptions
        );
        if (result.error) return { error: result.error };
        return { data: (result.data as ApiEnvelope<RegisterResponse>).data };
      },
      invalidatesTags: ["User"],
    }),

    logout: builder.mutation<void, void>({
      queryFn: async (_arg, api, extraOptions) => {
        const result = await localAuthQuery(
          { url: "/api/auth/logout", method: "POST" },
          api,
          extraOptions
        );
        if (result.error) return { error: result.error };
        return { data: undefined };
      },
      invalidatesTags: ["User"],
    }),

    // Hits the real backend (with the Authorization header baseApi injects)
    // — these don't touch the refresh cookie at all.
    getMe: builder.query<User, void>({
      query: () => "/auth/me",
      transformResponse: (res: ApiEnvelope<User>) => res.data,
      providesTags: ["User"],
    }),

    changePassword: builder.mutation<void, ChangePasswordRequest>({
      query: (body) => ({
        url: "/auth/change-password",
        method: "POST",
        body,
      }),
    }),
  }),
  overrideExisting: false,
});

export const {
  useLoginMutation,
  useRegisterMutation,
  useLogoutMutation,
  useGetMeQuery,
  useChangePasswordMutation,
} = authApi;

import { baseApi } from "@/store/api/baseApi";
import type {
  ApiEnvelope,
  ChangePasswordRequest,
  UpdateProfileRequest,
  User,
} from "@/types/api";

// Note: Module 1 (Auth) specced /auth/change-password for password changes,
// and authApi.changePassword still hits that route. This module's spec
// separately lists /users/password for the same purpose — a genuine
// contradiction between the two module specs, not something invented here.
// This account page uses updatePassword/users/password below, per this
// module's explicit instruction; authApi's version is left in place rather
// than deleted, since it was equally explicit in its own module. Confirm
// with the backend which one is real before shipping.
export const usersApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getProfile: builder.query<User, void>({
      query: () => "/users/profile",
      transformResponse: (res: ApiEnvelope<User>) => res.data,
      providesTags: ["User"],
    }),

    updateProfile: builder.mutation<User, UpdateProfileRequest>({
      query: (body) => ({ url: "/users/profile", method: "PUT", body }),
      transformResponse: (res: ApiEnvelope<User>) => res.data,
      invalidatesTags: ["User"],
    }),

    updatePassword: builder.mutation<void, ChangePasswordRequest>({
      query: (body) => ({ url: "/users/password", method: "PUT", body }),
    }),
  }),
  overrideExisting: false,
});

export const {
  useGetProfileQuery,
  useUpdateProfileMutation,
  useUpdatePasswordMutation,
} = usersApi;

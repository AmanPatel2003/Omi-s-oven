import { baseApi } from "@/store/api/baseApi";
import type { ApiEnvelope, StaffMember } from "@/types/api";

// Only what this module explicitly needs (GET /admin/staff?role=...) for
// the rider-assignment dropdown — the full Staff admin module (listed in
// the sidebar, not yet built) will likely expand this file with CRUD.
export const adminStaffApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getStaffByRole: builder.query<StaffMember[], string>({
      query: (role) => `/admin/staff?role=${role}`,
      transformResponse: (res: ApiEnvelope<StaffMember[]>) => res.data,
    }),
  }),
  overrideExisting: false,
});

export const { useGetStaffByRoleQuery } = adminStaffApi;

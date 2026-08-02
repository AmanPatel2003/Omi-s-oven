import { baseApi } from "@/store/api/baseApi";
import type {
  ApiEnvelope,
  CreateStaffRequest,
  CreateStaffResponse,
  StaffMember,
  StaffProfile,
  UpdateStaffRequest,
} from "@/types/api";

export const adminStaffApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getStaffByRole: builder.query<StaffMember[], string>({
      query: (role) => `/admin/staff?role=${role}`,
      transformResponse: (res: ApiEnvelope<StaffMember[]>) => res.data,
    }),

    getStaffList: builder.query<StaffProfile[], { role?: string } | void>({
      query: (params) =>
        `/admin/staff${params?.role ? `?role=${params.role}` : ""}`,
      transformResponse: (res: ApiEnvelope<StaffProfile[]>) => res.data,
      providesTags: (result) =>
        result
          ? [
              ...result.map((s) => ({ type: "User" as const, id: s.id })),
              { type: "User" as const, id: "STAFF_LIST" },
            ]
          : [{ type: "User" as const, id: "STAFF_LIST" }],
    }),

    getStaffById: builder.query<StaffProfile, string>({
      query: (id) => `/admin/staff/${id}`,
      transformResponse: (res: ApiEnvelope<StaffProfile>) => res.data,
      providesTags: (_result, _error, id) => [{ type: "User", id }],
    }),

    createStaff: builder.mutation<CreateStaffResponse, CreateStaffRequest>({
      query: (body) => ({ url: "/admin/staff", method: "POST", body }),
      transformResponse: (res: ApiEnvelope<CreateStaffResponse>) => res.data,
      invalidatesTags: [{ type: "User", id: "STAFF_LIST" }],
    }),

    updateStaff: builder.mutation<
      StaffProfile,
      { id: string } & UpdateStaffRequest
    >({
      query: ({ id, ...body }) => ({
        url: `/admin/staff/${id}`,
        method: "PUT",
        body,
      }),
      transformResponse: (res: ApiEnvelope<StaffProfile>) => res.data,
      invalidatesTags: (_result, _error, arg) => [
        { type: "User", id: arg.id },
        { type: "User", id: "STAFF_LIST" },
      ],
    }),

    deactivateStaff: builder.mutation<void, string>({
      query: (id) => ({ url: `/admin/staff/${id}/deactivate`, method: "POST" }),
      invalidatesTags: (_result, _error, id) => [
        { type: "User", id },
        { type: "User", id: "STAFF_LIST" },
      ],
    }),
  }),
  overrideExisting: false,
});

export const {
  useGetStaffByRoleQuery,
  useGetStaffListQuery,
  useGetStaffByIdQuery,
  useCreateStaffMutation,
  useUpdateStaffMutation,
  useDeactivateStaffMutation,
} = adminStaffApi;

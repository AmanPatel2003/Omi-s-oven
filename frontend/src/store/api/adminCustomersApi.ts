import { baseApi } from "@/store/api/baseApi";
import type {
  AdjustRewardPointsRequest,
  AdminCustomer,
  AdminCustomerDetail,
  AdminCustomerListParams,
  ApiEnvelope,
  Paginated,
} from "@/types/api";

function buildQuery(params: AdminCustomerListParams = {}): string {
  const search = new URLSearchParams();
  if (params.page) search.set("page", String(params.page));
  if (params.search) search.set("search", params.search);
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export const adminCustomersApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getAdminCustomers: builder.query<
      Paginated<AdminCustomer>,
      AdminCustomerListParams | void
    >({
      query: (params) => `/admin/customers${buildQuery(params ?? {})}`,
      transformResponse: (res: ApiEnvelope<Paginated<AdminCustomer>>) =>
        res.data,
      providesTags: (result) =>
        result
          ? [
              ...result.items.map((c) => ({ type: "User" as const, id: c.id })),
              { type: "User" as const, id: "CUSTOMER_LIST" },
            ]
          : [{ type: "User" as const, id: "CUSTOMER_LIST" }],
    }),

    getAdminCustomerById: builder.query<AdminCustomerDetail, string>({
      query: (id) => `/admin/customers/${id}`,
      transformResponse: (res: ApiEnvelope<AdminCustomerDetail>) => res.data,
      providesTags: (_result, _error, id) => [{ type: "User", id }],
    }),

    toggleCustomerBlock: builder.mutation<
      AdminCustomer,
      { id: string; isBlocked: boolean }
    >({
      query: ({ id, isBlocked }) => ({
        url: `/admin/customers/${id}/block`,
        method: "POST",
        body: { isBlocked },
      }),
      transformResponse: (res: ApiEnvelope<AdminCustomer>) => res.data,
      invalidatesTags: (_result, _error, arg) => [
        { type: "User", id: arg.id },
        { type: "User", id: "CUSTOMER_LIST" },
      ],
    }),

    adjustCustomerRewardPoints: builder.mutation<
      AdminCustomer,
      { id: string } & AdjustRewardPointsRequest
    >({
      query: ({ id, ...body }) => ({
        url: `/admin/customers/${id}/points`,
        method: "POST",
        body,
      }),
      transformResponse: (res: ApiEnvelope<AdminCustomer>) => res.data,
      invalidatesTags: (_result, _error, arg) => [{ type: "User", id: arg.id }],
    }),
  }),
  overrideExisting: false,
});

export const {
  useGetAdminCustomersQuery,
  useGetAdminCustomerByIdQuery,
  useToggleCustomerBlockMutation,
  useAdjustCustomerRewardPointsMutation,
} = adminCustomersApi;

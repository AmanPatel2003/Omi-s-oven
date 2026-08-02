import { baseApi } from "@/store/api/baseApi";
import type {
  AdminCustomOrder,
  ApiEnvelope,
  SetQuoteRequest,
} from "@/types/api";
import type { CustomOrderStatus } from "@/lib/constants";

export const adminCustomOrdersApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getAdminCustomOrders: builder.query<
      AdminCustomOrder[],
      CustomOrderStatus[] | void
    >({
      query: (statuses) => {
        if (!statuses || statuses.length === 0) return "/admin/custom-orders";
        const params = new URLSearchParams();
        statuses.forEach((s) => params.append("status", s));
        return `/admin/custom-orders?${params.toString()}`;
      },
      transformResponse: (res: ApiEnvelope<AdminCustomOrder[]>) => res.data,
      providesTags: (result) =>
        result
          ? [
              ...result.map((o) => ({
                type: "CustomOrder" as const,
                id: o.id,
              })),
              { type: "CustomOrder" as const, id: "ADMIN_LIST" },
            ]
          : [{ type: "CustomOrder" as const, id: "ADMIN_LIST" }],
    }),

    getAdminCustomOrderById: builder.query<AdminCustomOrder, string>({
      query: (id) => `/admin/custom-orders/${id}`,
      transformResponse: (res: ApiEnvelope<AdminCustomOrder>) => res.data,
      providesTags: (_result, _error, id) => [{ type: "CustomOrder", id }],
    }),

    setCustomOrderQuote: builder.mutation<
      AdminCustomOrder,
      { id: string } & SetQuoteRequest
    >({
      query: ({ id, ...body }) => ({
        url: `/admin/custom-orders/${id}/quote`,
        method: "POST",
        body,
      }),
      transformResponse: (res: ApiEnvelope<AdminCustomOrder>) => res.data,
      invalidatesTags: (_result, _error, arg) => [
        { type: "CustomOrder", id: arg.id },
        { type: "CustomOrder", id: "ADMIN_LIST" },
      ],
    }),
  }),
  overrideExisting: false,
});

export const {
  useGetAdminCustomOrdersQuery,
  useGetAdminCustomOrderByIdQuery,
  useSetCustomOrderQuoteMutation,
} = adminCustomOrdersApi;

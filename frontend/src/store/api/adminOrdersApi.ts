import { baseApi } from "@/store/api/baseApi";
import type {
  AdminOrder,
  AdminOrderListParams,
  ApiEnvelope,
  Paginated,
} from "@/types/api";
import type { OrderStatus } from "@/lib/constants";

function buildQuery(params: AdminOrderListParams = {}): string {
  const search = new URLSearchParams();
  if (params.page) search.set("page", String(params.page));
  if (params.status) search.set("status", params.status);
  if (params.from) search.set("from", params.from);
  if (params.to) search.set("to", params.to);
  if (params.search) search.set("search", params.search);
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

export const adminOrdersApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getAdminOrders: builder.query<
      Paginated<AdminOrder>,
      AdminOrderListParams | void
    >({
      query: (params) => `/admin/orders${buildQuery(params ?? {})}`,
      transformResponse: (res: ApiEnvelope<Paginated<AdminOrder>>) => res.data,
      providesTags: (result) =>
        result
          ? [
              ...result.items.map((o) => ({
                type: "Order" as const,
                id: o.id,
              })),
              { type: "Order" as const, id: "ADMIN_LIST" },
            ]
          : [{ type: "Order" as const, id: "ADMIN_LIST" }],
    }),

    getAdminOrderById: builder.query<AdminOrder, string>({
      query: (id) => `/admin/orders/${id}`,
      transformResponse: (res: ApiEnvelope<AdminOrder>) => res.data,
      providesTags: (_result, _error, id) => [{ type: "Order", id }],
    }),

    transitionOrderStatus: builder.mutation<
      AdminOrder,
      { id: string; status: OrderStatus }
    >({
      query: ({ id, status }) => ({
        url: `/admin/orders/${id}/status`,
        method: "POST",
        body: { status },
      }),
      transformResponse: (res: ApiEnvelope<AdminOrder>) => res.data,
      invalidatesTags: (_result, _error, arg) => [
        { type: "Order", id: arg.id },
        { type: "Order", id: "ADMIN_LIST" },
      ],
    }),

    assignRider: builder.mutation<AdminOrder, { id: string; riderId: string }>({
      query: ({ id, riderId }) => ({
        url: `/admin/orders/${id}/assign-rider`,
        method: "POST",
        body: { riderId },
      }),
      transformResponse: (res: ApiEnvelope<AdminOrder>) => res.data,
      invalidatesTags: (_result, _error, arg) => [
        { type: "Order", id: arg.id },
      ],
    }),
  }),
  overrideExisting: false,
});

export const {
  useGetAdminOrdersQuery,
  useGetAdminOrderByIdQuery,
  useTransitionOrderStatusMutation,
  useAssignRiderMutation,
} = adminOrdersApi;

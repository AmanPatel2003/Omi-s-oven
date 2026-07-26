import { baseApi } from "@/store/api/baseApi";
import type {
  ApiEnvelope,
  Cart,
  CreateOrderRequest,
  Order,
  OrderTracking,
  Paginated,
} from "@/types/api";

export const ordersApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    createOrder: builder.mutation<Order, CreateOrderRequest>({
      query: (body) => ({ url: "/orders", method: "POST", body }),
      transformResponse: (res: ApiEnvelope<Order>) => res.data,
      invalidatesTags: [{ type: "Order", id: "LIST" }, "Cart"],
    }),

    getOrders: builder.query<Paginated<Order>, { page?: number } | void>({
      query: (params) => `/orders${params?.page ? `?page=${params.page}` : ""}`,
      transformResponse: (res: ApiEnvelope<Paginated<Order>>) => res.data,
      providesTags: (result) =>
        result
          ? [
              ...result.items.map((o) => ({
                type: "Order" as const,
                id: o.id,
              })),
              { type: "Order" as const, id: "LIST" },
            ]
          : [{ type: "Order" as const, id: "LIST" }],
    }),

    getActiveOrders: builder.query<Order[], void>({
      query: () => "/orders/active",
      transformResponse: (res: ApiEnvelope<Order[]>) => res.data,
      providesTags: [{ type: "Order", id: "ACTIVE" }],
    }),

    getOrderById: builder.query<Order, string>({
      query: (id) => `/orders/${id}`,
      transformResponse: (res: ApiEnvelope<Order>) => res.data,
      providesTags: (_result, _error, id) => [{ type: "Order", id }],
    }),

    trackOrder: builder.query<OrderTracking, string>({
      query: (id) => `/orders/${id}/track`,
      transformResponse: (res: ApiEnvelope<OrderTracking>) => res.data,
    }),

    cancelOrder: builder.mutation<Order, string>({
      query: (id) => ({ url: `/orders/${id}/cancel`, method: "POST" }),
      transformResponse: (res: ApiEnvelope<Order>) => res.data,
      invalidatesTags: (_result, _error, id) => [
        { type: "Order", id },
        { type: "Order", id: "LIST" },
      ],
    }),

    reorder: builder.mutation<Cart, string>({
      query: (id) => ({ url: `/orders/${id}/reorder`, method: "POST" }),
      transformResponse: (res: ApiEnvelope<Cart>) => res.data,
      invalidatesTags: ["Cart"],
    }),
  }),
  overrideExisting: false,
});

export const {
  useCreateOrderMutation,
  useGetOrdersQuery,
  useGetActiveOrdersQuery,
  useGetOrderByIdQuery,
  useTrackOrderQuery,
  useCancelOrderMutation,
  useReorderMutation,
} = ordersApi;

import { baseApi } from "@/store/api/baseApi";
import type {
  ApiEnvelope,
  CreateCustomOrderRequest,
  CustomOrder,
} from "@/types/api";

export const customOrdersApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    createCustomOrder: builder.mutation<CustomOrder, CreateCustomOrderRequest>({
      query: (body) => ({ url: "/custom-orders", method: "POST", body }),
      transformResponse: (res: ApiEnvelope<CustomOrder>) => res.data,
      invalidatesTags: [{ type: "CustomOrder", id: "LIST" }],
    }),

    getCustomOrders: builder.query<CustomOrder[], void>({
      query: () => "/custom-orders",
      transformResponse: (res: ApiEnvelope<CustomOrder[]>) => res.data,
      providesTags: (result) =>
        result
          ? [
              ...result.map((o) => ({
                type: "CustomOrder" as const,
                id: o.id,
              })),
              { type: "CustomOrder" as const, id: "LIST" },
            ]
          : [{ type: "CustomOrder" as const, id: "LIST" }],
    }),

    getCustomOrderById: builder.query<CustomOrder, string>({
      query: (id) => `/custom-orders/${id}`,
      transformResponse: (res: ApiEnvelope<CustomOrder>) => res.data,
      providesTags: (_result, _error, id) => [{ type: "CustomOrder", id }],
    }),

    acceptQuote: builder.mutation<CustomOrder, string>({
      query: (id) => ({
        url: `/custom-orders/${id}/accept-quote`,
        method: "POST",
      }),
      transformResponse: (res: ApiEnvelope<CustomOrder>) => res.data,
      invalidatesTags: (_result, _error, id) => [
        { type: "CustomOrder", id },
        { type: "CustomOrder", id: "LIST" },
      ],
    }),
  }),
  overrideExisting: false,
});

export const {
  useCreateCustomOrderMutation,
  useGetCustomOrdersQuery,
  useGetCustomOrderByIdQuery,
  useAcceptQuoteMutation,
} = customOrdersApi;

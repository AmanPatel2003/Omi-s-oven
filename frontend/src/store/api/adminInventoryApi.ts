import { baseApi } from "@/store/api/baseApi";
import type {
  ApiEnvelope,
  InventoryAdjustmentRequest,
  InventoryItem,
  InventoryMovement,
} from "@/types/api";

export const adminInventoryApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getInventoryItems: builder.query<InventoryItem[], void>({
      query: () => "/admin/inventory",
      transformResponse: (res: ApiEnvelope<InventoryItem[]>) => res.data,
      providesTags: (result) =>
        result
          ? [
              ...result.map((i) => ({
                type: "Product" as const,
                id: `INV_${i.id}`,
              })),
              { type: "Product" as const, id: "INVENTORY_LIST" },
            ]
          : [{ type: "Product" as const, id: "INVENTORY_LIST" }],
    }),

    adjustInventory: builder.mutation<
      InventoryItem,
      { id: string } & InventoryAdjustmentRequest
    >({
      query: ({ id, ...body }) => ({
        url: `/admin/inventory/${id}`,
        method: "PUT",
        body,
      }),
      transformResponse: (res: ApiEnvelope<InventoryItem>) => res.data,
      invalidatesTags: (_result, _error, arg) => [
        { type: "Product", id: `INV_${arg.id}` },
        { type: "Product", id: "INVENTORY_LIST" },
      ],
    }),

    getInventoryMovements: builder.query<InventoryMovement[], string>({
      query: (id) => `/admin/inventory/${id}/movements`,
      transformResponse: (res: ApiEnvelope<InventoryMovement[]>) => res.data,
    }),
  }),
  overrideExisting: false,
});

export const {
  useGetInventoryItemsQuery,
  useAdjustInventoryMutation,
  useGetInventoryMovementsQuery,
} = adminInventoryApi;

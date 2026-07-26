import { baseApi } from "@/store/api/baseApi";
import type { AddressInput, ApiEnvelope, Address } from "@/types/api";

export const addressesApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getAddresses: builder.query<Address[], void>({
      query: () => "/users/addresses",
      transformResponse: (res: ApiEnvelope<Address[]>) => res.data,
      providesTags: (result) =>
        result
          ? [
              ...result.map((a) => ({ type: "Address" as const, id: a.id })),
              { type: "Address" as const, id: "LIST" },
            ]
          : [{ type: "Address" as const, id: "LIST" }],
    }),

    addAddress: builder.mutation<Address, AddressInput>({
      query: (body) => ({ url: "/users/addresses", method: "POST", body }),
      transformResponse: (res: ApiEnvelope<Address>) => res.data,
      invalidatesTags: [{ type: "Address", id: "LIST" }],
    }),

    updateAddress: builder.mutation<Address, { id: string } & AddressInput>({
      query: ({ id, ...body }) => ({
        url: `/users/addresses/${id}`,
        method: "PUT",
        body,
      }),
      transformResponse: (res: ApiEnvelope<Address>) => res.data,
      invalidatesTags: (_result, _error, arg) => [
        { type: "Address", id: arg.id },
        { type: "Address", id: "LIST" },
      ],
    }),

    deleteAddress: builder.mutation<void, string>({
      query: (id) => ({ url: `/users/addresses/${id}`, method: "DELETE" }),
      invalidatesTags: [{ type: "Address", id: "LIST" }],
    }),

    setDefaultAddress: builder.mutation<Address, string>({
      query: (id) => ({
        url: `/users/addresses/${id}/default`,
        method: "POST",
      }),
      transformResponse: (res: ApiEnvelope<Address>) => res.data,
      invalidatesTags: [{ type: "Address", id: "LIST" }],
    }),
  }),
  overrideExisting: false,
});

export const {
  useGetAddressesQuery,
  useAddAddressMutation,
  useUpdateAddressMutation,
  useDeleteAddressMutation,
  useSetDefaultAddressMutation,
} = addressesApi;

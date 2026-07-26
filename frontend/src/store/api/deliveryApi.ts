import { baseApi } from "@/store/api/baseApi";
import type { ApiEnvelope, DeliveryTracking } from "@/types/api";

export const deliveryApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    trackDelivery: builder.query<DeliveryTracking, string>({
      query: (orderId) => `/delivery/track/${orderId}`,
      transformResponse: (res: ApiEnvelope<DeliveryTracking>) => res.data,
      providesTags: (_result, _error, orderId) => [
        { type: "Delivery", id: orderId },
      ],
    }),
  }),
  overrideExisting: false,
});

export const { useTrackDeliveryQuery } = deliveryApi;

import { baseApi } from "@/store/api/baseApi";
import type {
  ApiEnvelope,
  BroadcastNotificationRequest,
  CampaignResult,
  SendNotificationRequest,
} from "@/types/api";

export const adminCampaignsApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    sendNotification: builder.mutation<CampaignResult, SendNotificationRequest>(
      {
        query: (body) => ({
          url: "/admin/notifications/send",
          method: "POST",
          body,
        }),
        transformResponse: (res: ApiEnvelope<CampaignResult>) => res.data,
      },
    ),

    broadcastNotification: builder.mutation<
      CampaignResult,
      BroadcastNotificationRequest
    >({
      query: (body) => ({
        url: "/admin/notifications/broadcast",
        method: "POST",
        body,
      }),
      transformResponse: (res: ApiEnvelope<CampaignResult>) => res.data,
    }),
  }),
  overrideExisting: false,
});

export const { useSendNotificationMutation, useBroadcastNotificationMutation } =
  adminCampaignsApi;

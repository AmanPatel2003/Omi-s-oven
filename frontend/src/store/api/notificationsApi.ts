import { baseApi } from "@/store/api/baseApi";
import type {
  ApiEnvelope,
  NotificationListResponse,
  NotificationPreferences,
} from "@/types/api";

export const notificationsApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getNotifications: builder.query<NotificationListResponse, void>({
      query: () => "/notifications",
      transformResponse: (res: ApiEnvelope<NotificationListResponse>) =>
        res.data,
      providesTags: (result) =>
        result
          ? [
              ...result.items.map((n) => ({
                type: "Notification" as const,
                id: n.id,
              })),
              { type: "Notification" as const, id: "LIST" },
            ]
          : [{ type: "Notification" as const, id: "LIST" }],
    }),

    markNotificationRead: builder.mutation<void, string>({
      query: (id) => ({ url: `/notifications/${id}/read`, method: "POST" }),
      invalidatesTags: (_result, _error, id) => [
        { type: "Notification", id },
        { type: "Notification", id: "LIST" },
      ],
    }),

    markAllNotificationsRead: builder.mutation<void, void>({
      query: () => ({ url: "/notifications/read-all", method: "POST" }),
      invalidatesTags: [{ type: "Notification", id: "LIST" }],
    }),

    getNotificationPreferences: builder.query<NotificationPreferences, void>({
      query: () => "/notifications/preferences",
      transformResponse: (res: ApiEnvelope<NotificationPreferences>) =>
        res.data,
      providesTags: [{ type: "Notification", id: "PREFERENCES" }],
    }),

    updateNotificationPreferences: builder.mutation<
      NotificationPreferences,
      Partial<NotificationPreferences>
    >({
      query: (body) => ({
        url: "/notifications/preferences",
        method: "PUT",
        body,
      }),
      transformResponse: (res: ApiEnvelope<NotificationPreferences>) =>
        res.data,
      async onQueryStarted(patch, { dispatch, queryFulfilled }) {
        const patchResult = dispatch(
          notificationsApi.util.updateQueryData(
            "getNotificationPreferences",
            undefined,
            (draft) => {
              Object.assign(draft, patch);
            },
          ),
        );
        try {
          await queryFulfilled;
        } catch {
          patchResult.undo();
        }
      },
    }),
  }),
  overrideExisting: false,
});

export const {
  useGetNotificationsQuery,
  useMarkNotificationReadMutation,
  useMarkAllNotificationsReadMutation,
  useGetNotificationPreferencesQuery,
  useUpdateNotificationPreferencesMutation,
} = notificationsApi;

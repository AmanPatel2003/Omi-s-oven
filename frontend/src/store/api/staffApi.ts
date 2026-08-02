import { baseApi } from "@/store/api/baseApi";
import type {
  ApiEnvelope,
  LocationPushRequest,
  MarkDeliveredRequest,
  MyAttendanceDay,
  StaffAssignedOrder,
  StaffClockStatus,
  StaffSalarySlip,
} from "@/types/api";

export const staffApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getClockStatus: builder.query<StaffClockStatus, void>({
      query: () => "/staff/clock-status",
      transformResponse: (res: ApiEnvelope<StaffClockStatus>) => res.data,
      providesTags: [{ type: "User", id: "MY_CLOCK_STATUS" }],
    }),

    clockIn: builder.mutation<StaffClockStatus, void>({
      query: () => ({ url: "/staff/clock-in", method: "POST" }),
      transformResponse: (res: ApiEnvelope<StaffClockStatus>) => res.data,
      invalidatesTags: [{ type: "User", id: "MY_CLOCK_STATUS" }],
    }),

    clockOut: builder.mutation<StaffClockStatus, void>({
      query: () => ({ url: "/staff/clock-out", method: "POST" }),
      transformResponse: (res: ApiEnvelope<StaffClockStatus>) => res.data,
      invalidatesTags: [{ type: "User", id: "MY_CLOCK_STATUS" }],
    }),

    getMyAttendance: builder.query<MyAttendanceDay[], void>({
      query: () => "/staff/my-attendance",
      transformResponse: (res: ApiEnvelope<MyAttendanceDay[]>) => res.data,
    }),

    getMySalary: builder.query<StaffSalarySlip[], void>({
      query: () => "/staff/my-salary",
      transformResponse: (res: ApiEnvelope<StaffSalarySlip[]>) => res.data,
    }),

    getAssignedOrders: builder.query<StaffAssignedOrder[], void>({
      query: () => "/staff/orders/assigned",
      transformResponse: (res: ApiEnvelope<StaffAssignedOrder[]>) => res.data,
      providesTags: (result) =>
        result
          ? [
              ...result.map((o) => ({ type: "Order" as const, id: o.id })),
              { type: "Order" as const, id: "MY_ASSIGNED" },
            ]
          : [{ type: "Order" as const, id: "MY_ASSIGNED" }],
    }),

    markPickedUp: builder.mutation<StaffAssignedOrder, string>({
      query: (orderId) => ({
        url: `/staff/orders/${orderId}/pickup`,
        method: "POST",
      }),
      transformResponse: (res: ApiEnvelope<StaffAssignedOrder>) => res.data,
      invalidatesTags: (_result, _error, orderId) => [
        { type: "Order", id: orderId },
        { type: "Order", id: "MY_ASSIGNED" },
      ],
    }),

    markDelivered: builder.mutation<
      StaffAssignedOrder,
      { orderId: string } & MarkDeliveredRequest
    >({
      query: ({ orderId, ...body }) => ({
        url: `/staff/orders/${orderId}/delivered`,
        method: "POST",
        body,
      }),
      transformResponse: (res: ApiEnvelope<StaffAssignedOrder>) => res.data,
      invalidatesTags: (_result, _error, arg) => [
        { type: "Order", id: arg.orderId },
        { type: "Order", id: "MY_ASSIGNED" },
      ],
    }),

    pushLocation: builder.mutation<void, LocationPushRequest>({
      query: (body) => ({ url: "/staff/location", method: "POST", body }),
    }),
  }),
  overrideExisting: false,
});

export const {
  useGetClockStatusQuery,
  useClockInMutation,
  useClockOutMutation,
  useGetMyAttendanceQuery,
  useGetMySalaryQuery,
  useGetAssignedOrdersQuery,
  useMarkPickedUpMutation,
  useMarkDeliveredMutation,
  usePushLocationMutation,
} = staffApi;

import { baseApi } from "@/store/api/baseApi";
import type {
  ApiEnvelope,
  AttendanceReportRow,
  MarkLeaveRequest,
  StaffAttendanceSummary,
  TodayAttendanceEntry,
  TodayAttendanceResponse,
} from "@/types/api";

export const adminAttendanceApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getTodayAttendance: builder.query<TodayAttendanceResponse, void>({
      query: () => "/admin/attendance/today",
      transformResponse: (res: ApiEnvelope<TodayAttendanceResponse>) =>
        res.data,
      providesTags: [{ type: "User", id: "ATTENDANCE_TODAY" }],
    }),

    getAttendanceReport: builder.query<AttendanceReportRow[], string>({
      query: (month) => `/admin/attendance/report?month=${month}`,
      transformResponse: (res: ApiEnvelope<AttendanceReportRow[]>) => res.data,
    }),

    clockInStaff: builder.mutation<TodayAttendanceEntry, string>({
      query: (staffId) => ({
        url: `/admin/attendance/${staffId}/clock-in`,
        method: "POST",
      }),
      transformResponse: (res: ApiEnvelope<TodayAttendanceEntry>) => res.data,
      invalidatesTags: [{ type: "User", id: "ATTENDANCE_TODAY" }],
    }),

    clockOutStaff: builder.mutation<TodayAttendanceEntry, string>({
      query: (staffId) => ({
        url: `/admin/attendance/${staffId}/clock-out`,
        method: "POST",
      }),
      transformResponse: (res: ApiEnvelope<TodayAttendanceEntry>) => res.data,
      invalidatesTags: [{ type: "User", id: "ATTENDANCE_TODAY" }],
    }),

    markLeave: builder.mutation<void, MarkLeaveRequest>({
      query: (body) => ({
        url: "/admin/attendance/leave",
        method: "POST",
        body,
      }),
      invalidatesTags: [{ type: "User", id: "ATTENDANCE_TODAY" }],
    }),

    getStaffAttendanceSummary: builder.query<StaffAttendanceSummary, string>({
      query: (staffId) => `/admin/attendance/summary/${staffId}`,
      transformResponse: (res: ApiEnvelope<StaffAttendanceSummary>) => res.data,
    }),
  }),
  overrideExisting: false,
});

export const {
  useGetTodayAttendanceQuery,
  useGetAttendanceReportQuery,
  useClockInStaffMutation,
  useClockOutStaffMutation,
  useMarkLeaveMutation,
  useGetStaffAttendanceSummaryQuery,
} = adminAttendanceApi;

import { baseApi } from "@/store/api/baseApi";
import type {
  ApiEnvelope,
  DashboardStats,
  HeatmapCell,
  LowStockItem,
  PendingOrderSummary,
  SalesPoint,
  PaginatedResponse,
  TopProduct,
} from "@/types/api";

export const adminDashboardApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getDashboardStats: builder.query<DashboardStats, void>({
      query: () => "/admin/dashboard/stats",
      transformResponse: (res: ApiEnvelope<DashboardStats>) => res.data,
    }),

    getDailySales: builder.query<SalesPoint[], void>({
      query: () => "/admin/dashboard/sales/daily",
      transformResponse: (res: ApiEnvelope<SalesPoint[]>) => res.data,
    }),

    getMonthlySales: builder.query<SalesPoint[], void>({
      query: () => "/admin/dashboard/sales/monthly",
      transformResponse: (res: ApiEnvelope<SalesPoint[]>) => res.data,
    }),

    getHourlyHeatmap: builder.query<HeatmapCell[], void>({
      query: () => "/admin/dashboard/heatmap",
      transformResponse: (res: ApiEnvelope<HeatmapCell[]>) => res.data,
    }),

    getTopProducts: builder.query<TopProduct[], void>({
      query: () => "/admin/dashboard/top-products",
      transformResponse: (res: ApiEnvelope<TopProduct[]>) => res.data,
    }),

    getLowStockAlerts: builder.query<LowStockItem[], void>({
      query: () => "/admin/dashboard/low-stock",
      transformResponse: (res: ApiEnvelope<LowStockItem[]>) => res.data,
      providesTags: [{ type: "Product", id: "LOW_STOCK" }],
    }),

    getPendingOrders: builder.query<
      PaginatedResponse<PendingOrderSummary>,
      void
    >({
      query: () => "/admin/dashboard/pending-orders",
      transformResponse: (
        res: ApiEnvelope<PaginatedResponse<PendingOrderSummary>>,
      ) => res.data,
      providesTags: [{ type: "Order", id: "PENDING" }],
    }),
  }),
  overrideExisting: false,
});

export const {
  useGetDashboardStatsQuery,
  useGetDailySalesQuery,
  useGetMonthlySalesQuery,
  useGetHourlyHeatmapQuery,
  useGetTopProductsQuery,
  useGetLowStockAlertsQuery,
  useGetPendingOrdersQuery,
} = adminDashboardApi;

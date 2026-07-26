import { baseApi } from "@/store/api/baseApi";
import type {
  AnalyticsDateRange,
  ApiEnvelope,
  CustomerGrowthPoint,
  DeliveryPerformance,
  ForecastRow,
  ProductSalesPoint,
  RevenueByCategory,
  RewardsStats,
} from "@/types/api";

function rangeQuery(range: AnalyticsDateRange): string {
  return `?from=${range.from}&to=${range.to}`;
}

export const adminAnalyticsApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getRevenueByCategory: builder.query<
      RevenueByCategory[],
      AnalyticsDateRange
    >({
      query: (range) =>
        `/admin/analytics/revenue-by-category${rangeQuery(range)}`,
      transformResponse: (res: ApiEnvelope<RevenueByCategory[]>) => res.data,
    }),

    getCustomerGrowth: builder.query<CustomerGrowthPoint[], AnalyticsDateRange>(
      {
        query: (range) =>
          `/admin/analytics/customer-growth${rangeQuery(range)}`,
        transformResponse: (res: ApiEnvelope<CustomerGrowthPoint[]>) =>
          res.data,
      },
    ),

    getProductSales: builder.query<
      ProductSalesPoint[],
      AnalyticsDateRange & { productId: string }
    >({
      query: ({ productId, ...range }) =>
        `/admin/analytics/product-sales/${productId}${rangeQuery(range)}`,
      transformResponse: (res: ApiEnvelope<ProductSalesPoint[]>) => res.data,
    }),

    getDeliveryPerformance: builder.query<
      DeliveryPerformance,
      AnalyticsDateRange
    >({
      query: (range) =>
        `/admin/analytics/delivery-performance${rangeQuery(range)}`,
      transformResponse: (res: ApiEnvelope<DeliveryPerformance>) => res.data,
    }),

    getRewardsStats: builder.query<RewardsStats, AnalyticsDateRange>({
      query: (range) => `/admin/analytics/rewards-stats${rangeQuery(range)}`,
      transformResponse: (res: ApiEnvelope<RewardsStats>) => res.data,
    }),

    getDemandForecast: builder.query<ForecastRow[], void>({
      query: () => "/admin/analytics/demand-forecast",
      transformResponse: (res: ApiEnvelope<ForecastRow[]>) => res.data,
    }),
  }),
  overrideExisting: false,
});

export const {
  useGetRevenueByCategoryQuery,
  useGetCustomerGrowthQuery,
  useGetProductSalesQuery,
  useGetDeliveryPerformanceQuery,
  useGetRewardsStatsQuery,
  useGetDemandForecastQuery,
} = adminAnalyticsApi;

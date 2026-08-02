import { baseApi } from "@/store/api/baseApi";
import type {
  AdminCoupon,
  ApiEnvelope,
  CouponUsageEntry,
  CreateCouponRequest,
  Paginated,
} from "@/types/api";

export const adminCouponsApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getAdminCoupons: builder.query<AdminCoupon[], void>({
      query: () => "/admin/coupons",
      transformResponse: (res: ApiEnvelope<AdminCoupon[]>) => res.data,
      providesTags: (result) =>
        result
          ? [
              ...result.map((c) => ({ type: "Coupon" as const, id: c.id })),
              { type: "Coupon" as const, id: "ADMIN_LIST" },
            ]
          : [{ type: "Coupon" as const, id: "ADMIN_LIST" }],
    }),

    createCoupon: builder.mutation<AdminCoupon, CreateCouponRequest>({
      query: (body) => ({ url: "/admin/coupons", method: "POST", body }),
      transformResponse: (res: ApiEnvelope<AdminCoupon>) => res.data,
      invalidatesTags: [{ type: "Coupon", id: "ADMIN_LIST" }],
    }),

    updateCoupon: builder.mutation<
      AdminCoupon,
      { id: string } & CreateCouponRequest
    >({
      query: ({ id, ...body }) => ({
        url: `/admin/coupons/${id}`,
        method: "PUT",
        body,
      }),
      transformResponse: (res: ApiEnvelope<AdminCoupon>) => res.data,
      invalidatesTags: (_result, _error, arg) => [
        { type: "Coupon", id: arg.id },
        { type: "Coupon", id: "ADMIN_LIST" },
      ],
    }),

    getCouponUsage: builder.query<
      Paginated<CouponUsageEntry>,
      { id: string; page?: number }
    >({
      query: ({ id, page }) =>
        `/admin/coupons/${id}/usage${page ? `?page=${page}` : ""}`,
      transformResponse: (res: ApiEnvelope<Paginated<CouponUsageEntry>>) =>
        res.data,
    }),
  }),
  overrideExisting: false,
});

export const {
  useGetAdminCouponsQuery,
  useCreateCouponMutation,
  useUpdateCouponMutation,
  useGetCouponUsageQuery,
} = adminCouponsApi;

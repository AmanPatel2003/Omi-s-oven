import { baseApi } from "@/store/api/baseApi";
import type {
  ApiEnvelope,
  Coupon,
  ValidateCouponRequest,
  ValidateCouponResponse,
} from "@/types/api";

export const couponsApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    validateCoupon: builder.mutation<
      ValidateCouponResponse,
      ValidateCouponRequest
    >({
      query: (body) => ({ url: "/coupons/validate", method: "POST", body }),
      transformResponse: (res: ApiEnvelope<ValidateCouponResponse>) => res.data,
    }),

    getActiveCoupons: builder.query<Coupon[], void>({
      query: () => "/coupons/active",
      transformResponse: (res: ApiEnvelope<Coupon[]>) => res.data,
      providesTags: [{ type: "Coupon", id: "LIST" }],
    }),
  }),
  overrideExisting: false,
});

export const { useValidateCouponMutation, useGetActiveCouponsQuery } =
  couponsApi;

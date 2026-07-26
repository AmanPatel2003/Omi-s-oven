import { baseApi } from "@/store/api/baseApi";
import type {
  ApiEnvelope,
  CreatePaymentResponse,
  Payment,
  VerifyPaymentRequest,
} from "@/types/api";

export const paymentsApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    createPayment: builder.mutation<CreatePaymentResponse, { orderId: string }>({
      query: (body) => ({ url: "/payments/create", method: "POST", body }),
      transformResponse: (res: ApiEnvelope<CreatePaymentResponse>) => res.data,
    }),

    verifyPayment: builder.mutation<Payment, VerifyPaymentRequest>({
      query: (body) => ({ url: "/payments/verify", method: "POST", body }),
      transformResponse: (res: ApiEnvelope<Payment>) => res.data,
      invalidatesTags: (_result, _error, arg) => [{ type: "Order", id: arg.orderId }],
    }),

    getPaymentByOrderId: builder.query<Payment, string>({
      query: (orderId) => `/payments/${orderId}`,
      transformResponse: (res: ApiEnvelope<Payment>) => res.data,
    }),
  }),
  overrideExisting: false,
});

export const {
  useCreatePaymentMutation,
  useVerifyPaymentMutation,
  useGetPaymentByOrderIdQuery,
} = paymentsApi;
import { baseApi } from "@/store/api/baseApi";
import type {
  ApiEnvelope,
  Cart,
  RedeemPointsRequest,
  RewardsSummary,
  RewardTier,
  RewardTransaction,
} from "@/types/api";

export const rewardsApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getRewardsSummary: builder.query<RewardsSummary, void>({
      query: () => "/rewards",
      transformResponse: (res: ApiEnvelope<RewardsSummary>) => res.data,
      providesTags: [{ type: "Reward", id: "SUMMARY" }],
    }),

    getRewardTransactions: builder.query<RewardTransaction[], void>({
      query: () => "/rewards/transactions",
      transformResponse: (res: ApiEnvelope<RewardTransaction[]>) => res.data,
      providesTags: [{ type: "Reward", id: "TRANSACTIONS" }],
    }),

    getRewardTiers: builder.query<RewardTier[], void>({
      query: () => "/rewards/tiers",
      transformResponse: (res: ApiEnvelope<RewardTier[]>) => res.data,
      providesTags: [{ type: "Reward", id: "TIERS" }],
    }),

    redeemPoints: builder.mutation<Cart, RedeemPointsRequest>({
      query: (body) => ({ url: "/rewards/redeem", method: "POST", body }),
      transformResponse: (res: ApiEnvelope<Cart>) => res.data,
      invalidatesTags: ["Cart", { type: "Reward", id: "SUMMARY" }],
    }),
  }),
  overrideExisting: false,
});

export const {
  useGetRewardsSummaryQuery,
  useGetRewardTransactionsQuery,
  useGetRewardTiersQuery,
  useRedeemPointsMutation,
} = rewardsApi;

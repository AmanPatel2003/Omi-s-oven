import { baseApi } from "@/store/api/baseApi";
import type {
  AddToCartRequest,
  ApiEnvelope,
  Cart,
  CartSummary,
  UpdateCartItemRequest,
} from "@/types/api";

export const cartApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getCart: builder.query<Cart, void>({
      query: () => "/cart",
      transformResponse: (res: ApiEnvelope<Cart>) => res.data,
      providesTags: ["Cart"],
    }),

    getCartSummary: builder.query<CartSummary, void>({
      query: () => "/cart/summary",
      transformResponse: (res: ApiEnvelope<CartSummary>) => res.data,
      providesTags: ["Cart"],
    }),

    addToCart: builder.mutation<Cart, AddToCartRequest>({
      query: (body) => ({ url: "/cart/add", method: "POST", body }),
      transformResponse: (res: ApiEnvelope<Cart>) => res.data,
      async onQueryStarted(arg, { dispatch, queryFulfilled }) {
        const patchResult = dispatch(
          cartApi.util.updateQueryData("getCart", undefined, (draft) => {
            const existing = draft.items.find(
              (i) =>
                i.productId === arg.productId &&
                i.variantId === (arg.variantId ?? null),
            );
            if (existing) {
              existing.quantity += arg.quantity;
              existing.lineTotal = existing.unitPrice * existing.quantity;
            } else {
              draft.items.push({
                id: `optimistic-${arg.productId}-${arg.variantId ?? "base"}`,
                productId: arg.productId,
                variantId: arg.variantId ?? null,
                name: "",
                image: null,
                unitPrice: 0,
                quantity: arg.quantity,
                lineTotal: 0,
                inStock: true,
                availableStock: arg.quantity,
              });
            }
          }),
        );
        try {
          await queryFulfilled;
        } catch {
          patchResult.undo();
        }
      },
      invalidatesTags: ["Cart"],
    }),

    updateCartItem: builder.mutation<Cart, UpdateCartItemRequest>({
      query: (body) => ({ url: "/cart/update", method: "POST", body }),
      transformResponse: (res: ApiEnvelope<Cart>) => res.data,
      async onQueryStarted({ itemId, quantity }, { dispatch, queryFulfilled }) {
        const patchResult = dispatch(
          cartApi.util.updateQueryData("getCart", undefined, (draft) => {
            const item = draft.items.find((i) => i.id === itemId);
            if (item) {
              item.quantity = quantity;
              item.lineTotal = item.unitPrice * quantity;
            }
          }),
        );
        try {
          await queryFulfilled;
        } catch {
          patchResult.undo();
        }
      },
      invalidatesTags: ["Cart"],
    }),

    removeFromCart: builder.mutation<Cart, string>({
      query: (productId) => ({
        url: `/cart/remove/${productId}`,
        method: "POST",
      }),
      transformResponse: (res: ApiEnvelope<Cart>) => res.data,
      async onQueryStarted(productId, { dispatch, queryFulfilled }) {
        const patchResult = dispatch(
          cartApi.util.updateQueryData("getCart", undefined, (draft) => {
            draft.items = draft.items.filter((i) => i.productId !== productId);
          }),
        );
        try {
          await queryFulfilled;
        } catch {
          patchResult.undo();
        }
      },
      invalidatesTags: ["Cart"],
    }),

    clearCart: builder.mutation<void, void>({
      query: () => ({ url: "/cart/clear", method: "POST" }),
      invalidatesTags: ["Cart"],
    }),

    applyCoupon: builder.mutation<Cart, { code: string }>({
      query: (body) => ({ url: "/cart/apply-coupon", method: "POST", body }),
      transformResponse: (res: ApiEnvelope<Cart>) => res.data,
      invalidatesTags: ["Cart"],
    }),

    removeCoupon: builder.mutation<Cart, void>({
      query: () => ({ url: "/cart/remove-coupon", method: "POST" }),
      transformResponse: (res: ApiEnvelope<Cart>) => res.data,
      invalidatesTags: ["Cart"],
    }),
  }),
  overrideExisting: false,
});

export const {
  useGetCartQuery,
  useGetCartSummaryQuery,
  useAddToCartMutation,
  useUpdateCartItemMutation,
  useRemoveFromCartMutation,
  useClearCartMutation,
  useApplyCouponMutation,
  useRemoveCouponMutation,
} = cartApi;
